from collections import defaultdict
import csv
import datetime
import getpass
import os
import sys
from pathlib import Path

import rich_click as click
from dotenv import load_dotenv
from loguru import logger

from elguason.configure_cron import configure
from elguason.download_facturas import download_comprobantes, DownloadComprobantesConfig
from elguason.facturacion_report import generate_report_from_invoices
from elguason.facturar import FacturacionParameters, facturar_sol
from elguason.pacientes import leer_pacientes, ruta_excel_pacientes
from elguason.planificar import (
    generar_plan_de_facturacion_mensual,
    write_plan,
    CATEGORIAS_MONOTRIBUTO,
    FACTURACION_MENSUAL_MONOTRIBUTO_POR_CATEGORIA,
    FACTURACION_ANUAL_MONOTRIBUTO_POR_CATEGORIA,
)


load_dotenv()


@click.group()
def app():
    """Manage your invoices"""

@click.group()
def report():
    """Entrypoing for commands about reports"""

@click.group()
def facturar():
    """Subcommand for commands about facturar"""



@click.command()
def sol():
    """Facturar a los pacientes del Excel 'pacientes.xlsx' del escritorio.

    No recibe parámetros: el CUIL y el facturador se leen del .env
    (variables CUIL y FACTURADOR) y los pacientes del Excel del escritorio,
    con las columnas:

        nombre y apellido | cuit | numero de sesiones | honorarios por sesion | medio de pago | total

    Por cada paciente emite una Factura C (como psicóloga, actividad 04) por el
    total (sesiones * honorarios), a consumidor final con el CUIT del paciente.
    """
    cuil = os.getenv('CUIL')
    facturador = os.getenv('FACTURADOR')
    password = _read_password()
    destination = Path.cwd() / 'comprobantes'
    allow_billing_past_invoices = False

    if cuil is None or facturador is None:
        logger.error("CUIL and/or FACTURADOR not set in .env")
        sys.exit(1)

    try:
        pacientes = leer_pacientes()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    facturas = []
    for paciente in pacientes:
        facturas.append(
            FacturacionParameters(
                cuil=cuil,
                password=password,
                facturador=facturador,
                service_name="Tratamiento",
                service_amount=paciente.total,
                service_units=paciente.numero_de_sesiones,
                payment_method=paciente.medio_de_pago or "Contado",
                cuit_receptor=paciente.cuit,
                punto_de_venta="0004-Olazabal Av. 5031 - Ciudad de Buenos Aires",
                actividad="04",
            )
        )

    if not facturas:
        click.echo(f"✅ No hay pacientes para facturar en {ruta_excel_pacientes()}")
        return

    facturar_sol(cuil, password, facturador, facturas, allow_billing_past_invoices, os.path.join(destination, ''))



@click.command()
@click.argument('start')
@click.argument('end')
@click.option('--cuil', default=os.getenv('CUIL'))
@click.option('--facturador', default=os.getenv('FACTURADOR'), help='Name as it is on AFIP, case sensitive')
@click.option('--destination', help='Destination folder of pdfs', default=os.getcwd())
@click.option('--autoconfirm', default=False, help='Autoconfirm without user interaction required')
def download(cuil, facturador, start, end, autoconfirm, destination):
    """Download invoces from START date to END date. (dd/mm/YYYY).

    Example:

        download "01/10/2021" "31/10/2021" --destionation comprobantes
    """
    passwd = _read_password()
    try:
        start_date = datetime.datetime.strptime(start, '%d/%m/%Y').date()
        end_date = datetime.datetime.strptime(end, '%d/%m/%Y').date()
    except ValueError:
        logger.error('La fecha ingresada no respeta el formato. Ejemplo: 17/03/2021')
        sys.exit(0)

    os.makedirs(destination, exist_ok=True)
    logger.info("Starting to download comprobantes")
    savepath = download_comprobantes(config=DownloadComprobantesConfig(
        cuil=cuil,
        password=passwd,
        facturador_name=facturador,
        start_date=start_date,
        end_date=end_date,
        askconfirmation=not autoconfirm,
        download_folder=destination
    ))
    click.echo(f"Comprobantes saved at {savepath}")


@click.command()
@click.argument('comprobantespath')
@click.option('--destination', help='Destination to save csv and json report', default=os.getcwd())
def build(comprobantespath, destination):
    """Build reports from pdfs stored in folder COMPROBANTESPATH

    Example:

        report comprobantes --destionation reports
    """
    folder = generate_report_from_invoices(comprobantespath, destination)
    click.echo(f"Report saved at {folder}")


@click.command()
@click.argument('csvreport')
def earnings(csvreport):
    """Generate earnings report based on built reports"""
    with open(csvreport, 'r') as f:
        reader = csv.DictReader(f)
        header = next(reader)
        by_month_year = defaultdict(lambda: 0)
        for row in reader:
            year, month, day = row['Fecha'].split('-')
            key = f'{year}-{month}'
            by_month_year[key] += int(row['Monto'])


    with open('facturacion_por_mes.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Total"])
        for key, value in by_month_year.items():
            writer.writerow((key, value))



@click.command()
@click.argument('hour')
@click.argument('spec')
@click.option('--log', help="Where to store logs for cron runs.", default='~/elguason.log')
@click.option('--allow-billing-past-invoices', help="Set this if you want to bill invoices earlier than today",
              default=False)
def automate(hour, spec, log, allow_billing_past_invoices):
    """Configure cron to periodically emit invoices specified by certain csv SPEC at certain HOUR

    Usage:
        crontador 18 ~/facturacionspec.csv
    """
    path = os.path.expanduser(log)
    spec_absolute_path = Path(spec).absolute().expanduser()
    cron = configure(hour, spec_absolute_path, path, allow_billing_past_invoices)
    logger.info(f'✅ Configured new cron as:\n{cron}\n'
                f'See more details with `crontab -l`')


def _read_password():
    return os.getenv('PASSWORD') or getpass.getpass(f'Password (Hidden input): ')



@click.command()
@click.option('--categoria', type=click.Choice(CATEGORIAS_MONOTRIBUTO), default=None)
@click.option('--gastomensual', type=click.IntRange(10_000), default=None)
@click.option('--destination', help="Where to save the plan",
              default=f'plan_mensual_{datetime.datetime.today():%b}.csv')
def create_plan(categoria, gastomensual, destination):
    """Generar plan de facturacion mensual acorde a gastos"""
    if not categoria and not gastomensual:
        click.echo("Tenés que especificar --categoria <CAT> o --gastomensual <GASTO>")
        sys.exit(1)
    if categoria and gastomensual:
        click.echo("No podés especificar --categoria y --gastomensual a la vez.")
        sys.exit(1)

    if categoria:
        gastomensual = FACTURACION_MENSUAL_MONOTRIBUTO_POR_CATEGORIA[categoria.upper()]

    plan = generar_plan_de_facturacion_mensual(gastomensual)
    total = sum(x.amount for x in plan)
    path = write_plan(plan, destination)
    click.echo(f"Your plan was saved at {path}. It will bill {total} this month.\n")


@click.command()
def categorias():
    # Categoria: X, Mensual, Anual
    for cat in CATEGORIAS_MONOTRIBUTO:
        facturacion_mensual = FACTURACION_MENSUAL_MONOTRIBUTO_POR_CATEGORIA[cat]
        facturacion_anual = FACTURACION_ANUAL_MONOTRIBUTO_POR_CATEGORIA[cat]
        print(f"Categoria {cat}\nMensual: {facturacion_mensual:_}, Anual {facturacion_anual:_}\n")



report.add_command(download)
report.add_command(build)
report.add_command(earnings)

facturar.add_command(sol)


app.add_command(create_plan)
app.add_command(report)
app.add_command(facturar)
app.add_command(categorias)


if __name__ == "__main__":
    app()

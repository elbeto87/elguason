from collections import defaultdict
import csv
import json
import datetime
import getpass
import os
import sys
from pathlib import Path

import click
import rich_click
from dotenv import load_dotenv
from loguru import logger

from elguason import titulo_de_servicio_generator
from elguason.configure_cron import configure
from elguason.download_facturas import download_comprobantes, DownloadComprobantesConfig
from elguason.facturacion_report import report_from_pdfs
from elguason.facturar import FacturacionParameters, facturar, facturar_multiples
from elguason.planificar import (
    generar_plan_de_facturacion_mensual, 
    generar_plan_de_facturacion_semestral,
    write_plan,
    CATEGORIAS_MONOTRIBUTO,
    FACTURACION_MENSUAL_MONOTRIBUTO_POR_CATEGORIA,
)

click.Command.format_help = rich_click.rich_format_help
click.Group.format_help = rich_click.rich_format_help


load_dotenv()

@click.group()
def app():
    pass


@app.command()
@click.option('--cuil', default=os.getenv('CUIL'))
@click.option('--servicio', prompt='Ingresa el titulo del servicio a facturar', default=titulo_de_servicio_generator())
@click.option('--monto', prompt='Ingresa el monto a facturar', default=10_000, type=click.IntRange(0))
@click.option('--facturador', default=os.getenv('FACTURADOR'))
@click.option('--cuitdestino', default=None, help="CUIT destinatario si monto excede limite de anonimato")
@click.option('--ptoventa', default=1)
@click.option('--destination', help='Destination folder of billing receipts', default=Path.cwd() / 'comprobantes')
@click.option('--autoconfirm', default=False)
def facturar_prompt(cuil, servicio, monto, facturador, cuitdestino, ptoventa, destination, autoconfirm):
    """Emitir factura mediante parametros provistos de forma interactiva"""
    passwd = _read_password()
    config = FacturacionParameters(
        cuil=cuil,
        password=passwd,
        facturador=facturador,
        service_name=servicio,
        cuit_receptor=cuitdestino,
        punto_de_venta=ptoventa,
        service_amount=monto,
        askconfirmation=not autoconfirm,
    )
    facturar(config=config, destination=os.path.join(destination, ''))


@app.command()
@click.argument('csvpath')
@click.option('--cuil', default=os.getenv('CUIL'))
@click.option('--facturador', default=os.getenv('FACTURADOR'))
@click.option('--destination', help='Destination folder of billing receipts', default=Path.cwd() / 'comprobantes')
@click.option('--allow-billing-past-invoices', help="Set this if you want to allow billing of services in the past",
              default=False, is_flag=True)
@click.option('--autoconfirm', default=False)
def facturar_from_monthly_csv(csvpath, cuil, facturador, destination, allow_billing_past_invoices, autoconfirm):
    """Emite facturas dado lo especificado en CSVPATH

    El csv debe tener la siguiente estructura:

        fecha,servicio,monto,cuit_destino,punto_de_venta
        01/01/2021,Honorarios,12300,,,

    Tanto cuit destino como punto de venta son opcionales.
    cuit_destino defaultea a vacia
    punto_de_venta a 1, que es el caso comun de un unico punto de venta
    """
    facturas = []
    password = _read_password()
    with open(csvpath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            factura_date = datetime.datetime.strptime(row['fecha'], '%d/%m/%Y').date()
            if factura_date > datetime.datetime.today().date():
                logger.warning(
                    f"Ignored an invoice set for {factura_date!s} as it is in the future. "
                    f"({row['servicio']} - {row['monto']})"
                )
                continue

            facturas.append(
                FacturacionParameters(
                    cuil=cuil,
                    password=password,
                    facturador=facturador,
                    date=datetime.datetime.strptime(row['fecha'], '%d/%m/%Y').date(),
                    service_name=row['servicio'],
                    service_amount=int(row['monto']),
                    cuit_receptor=row['cuit_destino'],
                    punto_de_venta=row['punto_de_venta'] or 1,
                    askconfirmation=not autoconfirm,
                )
            )

    facturar_multiples(cuil, password, facturador, facturas, allow_billing_past_invoices, os.path.join(destination, ''))


@app.command()
@click.argument('start')
@click.argument('end')
@click.option('--cuil', default=os.getenv('CUIL'))
@click.option('--facturador', default=os.getenv('FACTURADOR'), help='Name as it is on AFIP, case sensitive')
@click.option('--destination', help='Destination folder of pdfs', default=os.getcwd())
@click.option('--autoconfirm', default=False, help='Autoconfirm without user interaction required')
def download_facturas(cuil, facturador, start, end, autoconfirm, destination):
    """Download invoces from START date to END date. Dates must be on dd/mm/YYYY format.

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
        download_folder=destination or os.getcwd()
    ))
    click.echo(f"Comprobantes saved at {savepath}")


@app.command()
@click.argument('comprobantespath')
@click.option('--destination', help='Destination to save csv and json report', default=os.getcwd())
def build_report(comprobantespath, destination):
    """Build reports from pdfs stored in folder COMPROBANTESPATH

    Example:

        report comprobantes --destionation reports
    """
    folder = report_from_pdfs(comprobantespath, destination)
    click.echo(f"Report saved at {folder}")


@app.command()
@click.argument('hour')
@click.argument('spec')
@click.option('--log', help="Where to store logs for cron runs.", default='~/elguason.log')
@click.option('--allow-billing-past-invoices', help="Set this if you want to bill invoices earlier than today",
              default=False)
def configure_cron(hour, spec, log, allow_billing_past_invoices):
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


@app.command()
@click.argument('gastomensual', type=click.IntRange(10_000))
@click.argument('semester', type=click.INT)
@click.argument('year', type=click.INT, default=datetime.datetime.today().year)
@click.option('--destination', help="Where to save the plan", default='plan_semestral.csv')
def planificar(gastomensual, semester, year, destination):
    """Generar plan de facturacion semestral acorde a gastos"""
    plan = generar_plan_de_facturacion_semestral(gastomensual, semester=semester, year=year)
    total = sum(x.amount for x in plan)
    path = write_plan(plan, destination)
    click.echo(f"Your plan will bill {total} this semester.\n"
               f"Open {path} to review it so you can then bill from it with `facturarcsv {path}`")


@app.command()
@click.option('--categoria', type=click.Choice(CATEGORIAS_MONOTRIBUTO), default=None)
@click.option('--gastomensual', type=click.IntRange(10_000), default=None)
@click.option('--destination', help="Where to save the plan", 
              default=f'plan_mensual_{datetime.datetime.today().month}.csv')
def planificar_mes(categoria, gastomensual, destination):
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



@app.command()
@click.argument('csvreport')
def report_from_csv(csvreport):
    """Generar reporte de facturacion desde csv"""
    with open(csvreport, 'r') as f:
        reader = csv.DictReader(f)
        header = next(reader)
        by_month_year = defaultdict(lambda: 0)
        for row in reader:
            year, month, day = row['Fecha'].split('-')
            key = f'{year}-{month}'
            by_month_year[key] += int(row['Monto'])

    print(json.dumps(by_month_year))

if __name__ == "__main__":
    app()

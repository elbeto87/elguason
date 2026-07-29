import getpass
import os
import sys
from pathlib import Path

import rich_click as click
from dotenv import load_dotenv
from loguru import logger

from elguason.facturar import FacturacionParameters, facturar_sol
from elguason.pacientes import leer_pacientes, ruta_excel_pacientes


load_dotenv()


@click.group()
def app():
    """Manage your invoices"""

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

    Por cada paciente emite una Factura C (como psicóloga) por el
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

    facturar_sol(
        cuil=cuil,
        password=password,
        facturador=facturador,
        facturaciones=facturas,
        allow_billing_past_invoices=allow_billing_past_invoices,
        destination=os.path.join(destination, '')
    )


def _read_password():
    return os.getenv('PASSWORD') or getpass.getpass(f'Password (Hidden input): ')


# Registrar comando sol en el grupo facturar
facturar.add_command(sol)

# Registrar grupo facturar en la app principal
app.add_command(facturar)


if __name__ == "__main__":
    app()

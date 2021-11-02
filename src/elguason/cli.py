import datetime
import os
import click
from dotenv import load_dotenv
import getpass
import csv

from .main import FacturacionParameters, facturar, FacturacionProgramada, facturar_multiples


load_dotenv()


@click.command()
@click.option('--cuil', default=os.getenv('CUIL'))
@click.option('--servicio', prompt='Ingresa el titulo del servicio a facturar', default='Servicios Profesionales')
@click.option('--monto', prompt='Ingresa el monto a facturar', default=10_000, type=click.IntRange(0))
@click.option('--facturador', default=os.getenv('FACTURADOR'))
@click.option('--cuitdestino', default=None, help="CUIT destinatario si monto excede limite de anonimato")
@click.option('--ptoventa', default=1)
@click.option('--autoconfirm', default=False)
def myfactura(monto, servicio, cuil, facturador, cuitdestino, autoconfirm, ptoventa):
    passwd = _read_password()
    config = FacturacionParameters(
        cuil=cuil,
        password=passwd,
        facturador_name=facturador,
        service_name=servicio,
        cuit_receptor=cuitdestino,
        punto_de_venta=ptoventa,
        service_amount=monto,
        askconfirmation=not autoconfirm
    )
    facturar(config=config)


@click.command()
@click.argument('csvpath')
@click.option('--cuil', default=os.getenv('CUIL'))
@click.option('--facturador', default=os.getenv('FACTURADOR'))
@click.option('--autoconfirm', default=False)
def facturar_from_monthly_csv(csvpath, cuil, facturador, autoconfirm):
    # TODO: Prevenir doble facturacion.
    facturaciones = []
    with open(csvpath, 'r') as f:
        reader = csv.DictReader(f)
        facturaciones = [
            FacturacionProgramada(
                date=row['fecha'],
                factura=FacturacionParameters(
                    cuil=cuil,
                    password=_read_password(),
                    facturador_name=facturador,
                    service_name=row['servicio'],
                    service_amount=row['monto'],
                    cuit_receptor=row['cuit_destino'],
                    punto_de_venta=row['punto_de_venta'],
                )
            ) for row in reader
        ]

    from pprint import pprint

    for f in facturaciones:
        print(f.date, f.factura)


def _read_password():
    return os.getenv('PASSWORD') or getpass.getpass(f'Password (Hidden input): ')



if __name__ == "__main__":
    facturar_from_monthly_csv()

import os
import click
from dotenv.main import load_dotenv
import getpass

from elguason.main import FacturacionParameters, facturar


load_dotenv()


@click.command()
@click.option('--cuil', default=os.getenv('CUIL'))
@click.option('--servicio', prompt='Ingresa el titulo del servicio a facturar', default='Servicios Profesionales')
@click.option('--monto', prompt='Ingresa el monto a facturar', default=10_000)
@click.option('--facturador', default=os.getenv('FACTURADOR'))
@click.option('--cuitdestino', default=None, help="CUIT destinatario si monto excede limite de anonimato")
@click.option('--ptoventa', default=1)
@click.option('--autoconfirm', default=False)
def myfactura(monto, servicio, cuil, facturador, cuitdestino, autoconfirm, ptoventa):
    passwd = os.getenv('PASSWORD') or getpass.getpass(f'Password (Hidden input): ')
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


if __name__ == "__main__":
    myfactura()

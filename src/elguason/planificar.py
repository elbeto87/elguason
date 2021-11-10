import calendar
import csv
import datetime
import random
import statistics
from typing import List

FACTURACION_ANUAL_MONOTRIBUTO_POR_CATEGORIA = {
    'A': 370_000,
    'B': 550_000,
    'C': 770_000,
    'D': 1060_000,
    'E': 1400_000,
    'F': 1750_000,
    'G': 2100_000,
    'H': 2600_000,
}
FACTURACION_MENSUAL_MONOTRIBUTO_POR_CATEGORIA = {
    cat: int(val/12)
    for cat, val in FACTURACION_ANUAL_MONOTRIBUTO_POR_CATEGORIA.items()
}


def facturacion_mensual_por_categoria():
    for cat, fact in FACTURACION_MENSUAL_MONOTRIBUTO_POR_CATEGORIA.items():
        print(f'Categoria {cat}', f'${fact}')


def prompt():
    # Ver si podes ingresar categoria monotributo directamente
    gastos_mensuales = int(input("Gastos Mensuales: ") or 150_000)
    today = datetime.datetime.today()
    first, last = calendar.monthrange(today.year, today.month)
    monthdays = [datetime.date(today.year, today.month, daynum) for daynum in range(1, last + 1)]
    future_weekdays = [x for x in monthdays if x.day >= today.day and x.weekday() not in (5, 6)]
    dias_a_facturar = len(future_weekdays)
    por_dia = gastos_mensuales / dias_a_facturar
    return future_weekdays, por_dia


def num_per_day_with_offset(num, limit=12500):
    return int(min(num + random.randint(-2500, 2500), limit - random.randint(100, 1000)))


def write(future_weekdays: List[datetime.date], facturacion_por_dia):
    with open('planificacion.csv', 'w') as f:
        writer = csv.writer(f)
        header = ['fecha', 'servicio', 'monto', 'cuit_destino', 'punto_de_venta']
        writer.writerow(header)
        total = 0

        normal_dist_from_facturacion_por_dia = statistics.NormalDist(mu=facturacion_por_dia, sigma=2000)
        amounts = normal_dist_from_facturacion_por_dia.samples(n=len(future_weekdays))

        for day, amount in zip(future_weekdays, amounts):
            total += amount
            row = [day.strftime('%d/%m/%Y'), 'Servicios Profesionales', amount, '', '']
            writer.writerow(row)

        print(f'La planificacion emitirá {len(future_weekdays)} facturas por un monto total de {total}')


def read():
    with open('planificacion.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            print(row)


weekdays, pordia = prompt()
write(weekdays, pordia)
read()

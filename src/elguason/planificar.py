import calendar
import csv
import datetime
import statistics
from typing import List, Tuple
from elguason import titulo_de_servicio_generator


FACTURACION_ANUAL_MONOTRIBUTO_POR_CATEGORIA = {
    # See https://www.afip.gob.ar/monotributo/categorias.asp
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


def generar_plan_de_facturacion(gastos_mensuales) -> List[Tuple[datetime.date, float]]:
    billable_days: List[datetime.date] = generate_billable_days()
    montos_por_dia = generar_facturacion_por_dia(gastos_mensuales, billable_days)
    return montos_por_dia


def generate_billable_days():
    """A day is billable if it is a future working day in the same month than current date"""
    today = datetime.datetime.today()
    _, lastdayofmonth = calendar.monthrange(today.year, today.month)
    monthdays = [datetime.date(today.year, today.month, daynum) for daynum in range(1, lastdayofmonth + 1)]
    future_weekdays = [x for x in monthdays if x.day >= today.day and x.weekday() not in (5, 6)]
    return future_weekdays


def generar_facturacion_por_dia(
        gastos_mensuales, billable_days: List[datetime.date]
) -> List[Tuple[datetime.date, float]]:
    """Dada una distribucion normal, genera cant_dias muestras respetando esa dist. normal"""
    cant_dias = len(billable_days)
    facturacion_por_dia = gastos_mensuales / cant_dias
    normal_dist_from_facturacion_por_dia = statistics.NormalDist(mu=facturacion_por_dia, sigma=1500)
    amounts = normal_dist_from_facturacion_por_dia.samples(n=cant_dias)
    return list(zip(billable_days, [int(x) for x in amounts]))


def write_plan(bill_by_day, path='planificacion.csv'):
    with open(path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['fecha', 'servicio', 'monto', 'cuit_destino', 'punto_de_venta']
        writer.writerow(header)
        for day, amount in bill_by_day:
            row = [day.strftime('%d/%m/%Y'), titulo_de_servicio_generator(), amount, '', '']
            writer.writerow(row)

    return path

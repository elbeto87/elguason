import calendar
import csv
import datetime
import itertools
import statistics
from collections import namedtuple
from typing import List

from elguason import titulo_de_servicio_generator


FacturacionDia = namedtuple('FacturacionDia', 'date amount')


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


def generar_plan_de_facturacion(gastos_mensuales) -> List[FacturacionDia]:
    days: List[datetime.date] = _get_current_month_dates()
    billable_days = [d for d in days if d.weekday() not in (5, 6)]
    montos_por_dia = _generar_facturacion_por_dia(gastos_mensuales, billable_days)
    return montos_por_dia


def generar_plan_de_facturacion_semestral(gastos_mensuales, semester: int, year) -> List[FacturacionDia]:
    assert semester in (1, 2), f"Semester must be either 1 or 2, not {semester!r}"
    months_by_semester = {1: [1, 2, 3, 4, 5, 6], 2: [7, 8, 9, 10, 11, 12]}
    year = year or datetime.datetime.today().year
    facturacion_mes_a_mes = [_generar_plan_de_facturacion_mensual(gastos_mensuales, year, mes) 
                             for mes in months_by_semester[semester]] 
    return list(itertools.chain.from_iterable(facturacion_mes_a_mes))


def _generar_plan_de_facturacion_mensual(gastos_mensuales, year, month) -> List[FacturacionDia]:
    _, lastdayofmonth = calendar.monthrange(year, month)
    billable_days = [datetime.date(year, month, daynum)
                     for daynum in range(1, lastdayofmonth + 1)]
    billable_days = [x for x in billable_days if x.weekday() not in (5, 6)]
    montos_por_dia = _generar_facturacion_por_dia(gastos_mensuales, billable_days)
    return montos_por_dia


def _generate_billable_days_in_the_future():
    """A day is billable if it is a future working day in the same month as the current date"""
    today = datetime.datetime.today()
    dates = _get_current_month_dates()
    return [
        date for date in dates
        if date.day >= today.day and date.weekday() not in (5, 6)
    ]


def _get_current_month_dates():
    """Get all dates of the current month"""
    today = datetime.datetime.today()
    _, lastdayofmonth = calendar.monthrange(today.year, today.month)
    billable_days = [datetime.date(today.year, today.month, daynum) 
                     for daynum in range(1, lastdayofmonth + 1)]
    return billable_days


def _generar_facturacion_por_dia(
        gastos_mensuales, billable_days: List[datetime.date]
) -> List[FacturacionDia]:
    """Genera montos de factura mediante una distribucion normal con mu=fact_mensual/dias"""
    cant_dias = len(billable_days)
    facturacion_por_dia = gastos_mensuales / cant_dias
    amounts = statistics.NormalDist(mu=facturacion_por_dia, sigma=1500).samples(n=cant_dias)

    return [
        FacturacionDia(date, max(round(int(amount), -1), 1000))  # Avoid negative or empty invoices
        for date, amount in zip(billable_days, amounts)
    ]


def write_plan(bill_by_day: List[FacturacionDia], path='planificacion.csv'):
    with open(path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['fecha', 'servicio', 'monto', 'cuit_destino', 'punto_de_venta']
        writer.writerow(header)
        for day, amount in bill_by_day:
            row = [day.strftime('%d/%m/%Y'), titulo_de_servicio_generator(), amount, '', '']
            writer.writerow(row)

    return path

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
    'A': 1_414_762,   # 120k
    'B': 2_103_000, # 175k
    'C': 2_944_000, # 245k
    'D': 3_656_000, # 305k
    'E': 4_305_000, # 358k
    'F': 5_382_000, # 448k
    'G': 6_458_000, # 538k
    'H': 7_996_000, # 666k
}
FACTURACION_MENSUAL_MONOTRIBUTO_POR_CATEGORIA = {
    cat: int(val/12)
    for cat, val in FACTURACION_ANUAL_MONOTRIBUTO_POR_CATEGORIA.items()
}


CATEGORIAS_MONOTRIBUTO = list(FACTURACION_ANUAL_MONOTRIBUTO_POR_CATEGORIA.keys())


def generar_plan_de_facturacion_mensual(gastos_mensuales) -> List[FacturacionDia]:
    days: List[datetime.date] = _get_current_month_dates()
    billable_days = [d for d in days if d.weekday() not in (5, 6)]
    montos_por_dia = _generar_facturacion_por_dia(gastos_mensuales, billable_days)
    return montos_por_dia


def _generar_plan_de_facturacion_mensual(gastos_mensuales, year, month) -> List[FacturacionDia]:
    _, lastdayofmonth = calendar.monthrange(year, month)
    billable_days = [datetime.date(year, month, daynum)
                     for daynum in range(1, lastdayofmonth + 1)]
    billable_days = [x for x in billable_days if x.weekday() not in (5, 6)]
    montos_por_dia = _generar_facturacion_por_dia(gastos_mensuales, billable_days)
    return montos_por_dia


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

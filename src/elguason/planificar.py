import calendar
import csv
import datetime
import random

FACTURACION_MONOTRIBUTO = {
    #
}
# Ver si podes ingresar categoria monotributo directamente
gastos_mensuales = int(input("Gastos Mensuales: ") or 150_000)
por_dia = gastos_mensuales / 20
facturacion_por_dia_randomized = por_dia + random.randint(100, 2000) - random.randint(200, 400)
print(f'Deberias facturar {por_dia} por dia habil para justificar esos gastos')

today = datetime.datetime.today()
first, last = calendar.monthrange(today.year, today.month)
monthdays = [datetime.date(today.year, today.month, daynum) for daynum in range(1, last + 1)]
future_weekdays = [x for x in monthdays if x.day >= today.day and x.weekday() not in (5, 6)]
dias_a_facturar = len(future_weekdays)
por_dia = gastos_mensuales / dias_a_facturar


def num_per_day_with_offset(num, limit=12500):
    return int(min(num + random.randint(-2500, 2500), limit - random.randint(100, 1000)))


with open('planificacion.csv', 'w') as f:
    writer = csv.writer(f)
    header = ['fecha', 'servicio', 'monto', 'cuit_destino', 'punto_de_venta']
    writer.writerow(header)
    total = 0
    for day in future_weekdays:
        monto = num_per_day_with_offset(por_dia)
        total += monto
        row = [day.strftime('%d/%m/%Y'), 'Servicios Profesionales', monto, '', '']
        writer.writerow(row)

    print(f'La planificacion emitirá {dias_a_facturar} facturas por un monto total de {total}')

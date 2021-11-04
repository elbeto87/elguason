import csv
import datetime
import glob
import json
import re
import warnings
from dataclasses import dataclass
from typing import List

from pdfminer.high_level import extract_text
from pdfminer.pdfdocument import PDFTextExtractionNotAllowedWarning


@dataclass
class Factura:
    monto: int
    fecha: datetime.date


def read(pdf_path: str) -> Factura:
    """Dado un pdf de factura C de AFIP, obtiene su monto y la fecha de facturacion"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=PDFTextExtractionNotAllowedWarning)
        text = extract_text(pdf_path)

    #                                  $\n\n1200,00\n\n -> 1200 Ignora decimales.
    monto = re.search(r'Importe Total: \$\s*(\d+)\s*', text).group(1)
    fecha = re.search(r'Fecha de Emisión:\s*(.*)\s*', text).group(1)
    fecha_date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()
    return Factura(fecha=fecha_date, monto=int(monto))


facturas = []
for pdf in glob.glob('*.pdf'):
    facturas.append(read(pdf))


def dump_to_csv(facturas: List[Factura], facturas_csv_path='facturas.csv'):
    with open(facturas_csv_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['Fecha', 'Monto'])
        for factura in facturas:
            writer.writerow([factura.fecha, factura.monto])

    return facturas_csv_path


def dump_to_json(facturas: List[Factura], saveas='facturas.json'):
    facturasdict = sorted([
        {'fecha': factura.fecha.strftime('%d/%m/%Y'), 'monto': factura.monto}
        for factura in facturas
    ], key=lambda key: key['fecha'])
    with open(saveas, 'w') as f:
        json.dump(facturasdict, f, indent=2, ensure_ascii=False)

    return saveas


total = sum(x.monto for x in facturas)
print(sorted(facturas, key=lambda x: x.fecha))
print('Total Facturado:', total)
dump_to_csv(facturas)
dump_to_json(facturas)

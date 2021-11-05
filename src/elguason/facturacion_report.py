import csv
import datetime
import glob
import json
import os.path
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


def extract_info_factura_from_pdf(pdf_path: str) -> Factura:
    """Dado un pdf de factura C de AFIP, obtiene su monto y la fecha de facturacion"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=PDFTextExtractionNotAllowedWarning)
        text = extract_text(pdf_path)

    #                                  $\n\n1200,00\n\n -> 1200 Ignora decimales.
    monto = re.search(r'Importe Total: \$\s*(\d+)\s*', text).group(1)
    fecha = re.search(r'Fecha de Emisión:\s*(.*)\s*', text).group(1)
    fecha_date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()
    return Factura(fecha=fecha_date, monto=int(monto))


def dump_to_csv(facturas: List[Factura], saveas='facturas.csv'):
    facturas.sort(key=lambda x: x.fecha)
    with open(saveas, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['Fecha', 'Monto'])
        for factura in facturas:
            writer.writerow([factura.fecha, factura.monto])

    return saveas


def dump_to_json(facturas: List[Factura], saveas='facturas.json'):
    facturasjson = [
        {'fecha': factura.fecha, 'monto': factura.monto}
        for factura in facturas
    ]
    orderedfacturas = sorted(facturasjson, key=lambda x: x['fecha'])

    with open(saveas, 'w') as f:
        json.dump(orderedfacturas, f, indent=2, ensure_ascii=False,
                  default=lambda x: x.strftime('%Y/%m/%d'))

    return saveas


def report_from_pdfs(folder: str, report_folder='reports'):
    files = glob.glob(f'{folder}/*.pdf')
    if not files:
        print(f'No hay PDFs de facturas en la carpeta indicada ({folder})')
        return

    facturas = [extract_info_factura_from_pdf(f) for f in files]
    os.makedirs(report_folder, exist_ok=True)
    date = datetime.datetime.today().date()
    dump_to_csv(facturas, saveas=f'{report_folder}/facturas-{date}.csv')
    dump_to_json(facturas, saveas=f'{report_folder}/facturas-{date}.json')
    return report_folder

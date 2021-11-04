import datetime
import glob
import re
import warnings
from dataclasses import dataclass
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

total = sum(x.monto for x in facturas)
print(sorted(facturas, key=lambda x: x.fecha))
print('Total Facturado:', total)

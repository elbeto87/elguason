import datetime
from dataclasses import dataclass
import time
from decimal import Decimal
from typing import List

from playwright.sync_api import Playwright, sync_playwright


@dataclass
class FacturacionParameters:
    cuil: str
    password: str
    facturador_name: str
    service_name: str
    service_amount: Decimal
    cuit_receptor: str
    punto_de_venta: int
    askconfirmation: bool = True
    date: datetime.date = datetime.datetime.today().date()

    def __str__(self):
        base = f'Factura de {self.facturador_name} por "{self.service_name}" por un monto de ${self.service_amount} '
        base += f'para {self.cuit_receptor}' if self.cuit_receptor else ''
        return base


LIMITE_FACTURACION_ANONIMA = 12500


def run_facturacion(
    plwright: Playwright,
    config: FacturacionParameters,
) -> None:
    if config.service_amount > LIMITE_FACTURACION_ANONIMA and not config.cuit_receptor:
        raise ValueError(f'Para facturar {config.service_amount} se requiere CUIT de consumidor final')
    today = datetime.datetime.today().date()
    if config.date > today:
        raise ValueError(f"No se puede emitir facturas para el futuro. "
                         f"Hoy es {today}, per la factura es para el {config.date}")
    if (today - config.date) > datetime.timedelta(days=10):
        raise ValueError("No se puede facturar servicios realizados hace mas de 10 dias")

    browser = plwright.chromium.launch(headless=False, slow_mo=1000)
    context = browser.new_context(
        accept_downloads=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    )
    print('Abriendo página monotributo..')
    page = context.new_page()
    page.goto("https://auth.afip.gov.ar/contribuyente_/login.xhtml?action=SYSTEM&system=admin_mono")

    print('Ingresando al sitio..')
    page.fill("input[name=\"F1:username\"]", config.cuil)
    page.press("input[name=\"F1:username\"]", "Enter")
    page.fill("input[name=\"F1:password\"]", config.password)

    with page.expect_navigation():
        page.press("input[name=\"F1:password\"]", "Enter")

    print('Ingresando a micrositio de facturación')
    with page.expect_navigation():
        with page.expect_popup() as popup_info:
            page.click("text=Emitir Factura")
        page1 = popup_info.value

    facturador = config.facturador_name.upper()
    print(f'Buscando boton de monotributista para el cual tributar con nombre {facturador}')
    page1.click(f"input[role=\"button\"]:has-text(\"{facturador}\")")
    page1.click("a[role=\"button\"]:has-text(\"Generar Comprobantes\")")

    print('Eligiendo punto de venta y tipo de factura')
    page1.select_option("select[name=\"puntoDeVenta\"]", str(config.punto_de_venta))

    # Wait it automatically selects Factura C on second dropdown menu
    time.sleep(2)
    page1.click("text=Continuar >")

    print('Ingresando servicio como tipo de facturacion')
    # Facturacion de Servicios
    servicios = "2"
    page1.select_option("select[name=\"idConcepto\"]", servicios)

    # Elegir periodo a facturar. Defaults to today
    if config.date != today:
        # Elegir facturacion para dia anterior
        date_str = config.date.strftime('%d/%m/%Y')
        page1.fill("input[name=\"periodoFacturadoDesde\"]", date_str)
        page1.fill("input[name=\"periodoFacturadoHasta\"]", date_str)
        # El dia de vencimiento debe ser hoy, sino no vale facturarlo

    page1.click("text=Continuar >")

    print(
        f'Facturando {config.service_name} por un monto de {config.service_amount} '
        f'para consumidor final con pago al contado'
    )
    consumidor_final = "5"
    page1.select_option("select[name=\"idIVAReceptor\"]", consumidor_final)

    if config.cuit_receptor:
        page1.click("input[name=\"nroDocReceptor\"]")
        page1.fill("input[name=\"nroDocReceptor\"]", config.cuit_receptor)

    # Chequear Checkbox de Contado
    page1.check("input[name=\"formaDePago\"]")
    page1.click("text=Continuar >")

    page1.click("textarea[name=\"detalleDescripcion\"]")
    page1.fill("textarea[name=\"detalleDescripcion\"]", config.service_name)

    page1.click("input[name=\"detallePrecio\"]")
    page1.fill("input[name=\"detallePrecio\"]", str(config.service_amount))

    page1.click("text=Continuar >")

    if config.askconfirmation:
        resp = input('Presiona ENTER para facturar, o cualquier otra tecla para cancelar\n')
        if resp != '':
            print('Cancelando Facturacion')
            exit(0)

    # Clickear confirmar y aceptar el popup
    page1.once("dialog", lambda dialog: dialog.accept())
    page1.click("text=Confirmar Datos...")

    # Imprimir comprobante con nombre autogenerado por AFIP
    with page1.expect_download() as download_info:
        page1.click("text=Imprimir...")

    download = download_info.value
    download.save_as(download.suggested_filename)
    print(f"File saved @ {download.suggested_filename}")

    context.close()
    browser.close()


def facturar(config: FacturacionParameters):
    with sync_playwright() as playwright:
        print("Inicio de facturacion 📝")
        run_facturacion(playwright, config=config)
        print("Facturacion finalizada ✨")


def facturar_multiples(facturaciones_por_dia: List[FacturacionParameters]):
    # TODO: Codegen browser to generate multiple facturas at once
    # Or perhaps just invoke the same run script N times.
    pass

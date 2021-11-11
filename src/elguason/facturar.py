import datetime
import json
from dataclasses import dataclass
import time
from pathlib import Path
from typing import List

from loguru import logger
from playwright.sync_api import sync_playwright


@dataclass
class FacturacionParameters:
    cuil: str
    password: str
    facturador: str
    service_name: str
    service_amount: int
    cuit_receptor: str
    punto_de_venta: int
    askconfirmation: bool = True
    date: datetime.date = datetime.datetime.today().date()

    def __str__(self):
        base = f"Factura de '{self.facturador}' por '{self.service_name}' por un monto de ${self.service_amount} "
        base += f'para {self.cuit_receptor}' if self.cuit_receptor else ''
        return base

    __repr__ = __str__

    def to_dict(self):
        return {
            'cuil': self.cuil,
            'service_name': self.service_name,
            'service_amount': self.service_amount,
            'cuit_receptor': self.cuit_receptor,
            'date': self.date.strftime('%Y-%m-%d')
            # We purposely ignore some attributes
            # As we want invoice uniqueness judged only
            # by the attributes above to be extra safe of double billing
        }

    def to_json(self):
        return json.dumps(self.to_dict())


LIMITE_FACTURACION_ANONIMA = 12500
HERE = Path(__file__).absolute().parent
invoicespath = HERE / '.facturaciones_realizadas.json'


def facturar(config: FacturacionParameters, destination):
    # Validate
    validate_facturacion_config(config, allow_billing_past_invoices=False)

    # Execute
    with sync_playwright() as playwright:
        logger.info("Inicio de facturacion 📝")
        browser = playwright.chromium.launch(headless=False, slow_mo=1000)
        run_facturacion(browser, config, destination)
        browser.close()
        logger.info("Facturacion finalizada ✨")

    mark_invoices_as_already_billed(configs=[config])


def facturar_multiples(
        cuil, password, facturador,
        facturaciones_por_dia: List[FacturacionParameters],
        allow_billing_past_invoices: bool,
        destination: str,
):
    # Validate
    validate_we_dont_repeat_any_invoice(facturaciones_por_dia)
    for facturacion_config in facturaciones_por_dia:
        validate_facturacion_config(facturacion_config, allow_billing_past_invoices)

    # Execute
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=1000)
        logger.info("Inicio de facturacion multiple 📝")
        run_facturacion_multiple(browser, cuil, password, facturador, facturaciones_por_dia, destination)
        logger.info("Facturaciones finalizadas ✨")
        browser.close()

    mark_invoices_as_already_billed(facturaciones_por_dia)


def run_facturacion(
    browser,
    config: FacturacionParameters,
    destination: str,
) -> None:
    context = browser.new_context(
        accept_downloads=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    )
    page = login(config.cuil, config.password, context)
    page1 = enter_facturacion_microsite(page)

    elegir_facturador(config.facturador, page1)
    generar_factura(config, page1)
    confirmar_factura(config, page1)
    descargar_factura(page1, destination)

    context.close()


def run_facturacion_multiple(browser, cuil, password, facturador, facturaciones_por_dia, destination):
    context = browser.new_context(
        accept_downloads=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    )
    logger.info("Login into AFIP")
    page = login(cuil, password, context)
    logger.info("Login into facturacion microsite")
    page1 = enter_facturacion_microsite(page)
    logger.info(f"Choosing facturador button by the provided name={facturador}")
    elegir_facturador(facturador, page1)
    logger.info("Start generating invoices")
    repeat_facturacion(page1, facturaciones_por_dia, destination)
    context.close()


def login(cuil, password, context):
    logger.info('Abriendo página monotributo..')
    page = context.new_page()
    page.goto("https://auth.afip.gov.ar/contribuyente_/login.xhtml?action=SYSTEM&system=admin_mono")
    logger.info('Ingresando al sitio..')
    page.fill("input[name=\"F1:username\"]", cuil)
    page.press("input[name=\"F1:username\"]", "Enter")
    page.fill("input[name=\"F1:password\"]", password)
    with page.expect_navigation():
        page.press("input[name=\"F1:password\"]", "Enter")

    return page


def enter_facturacion_microsite(page):
    logger.info('Ingresando a micrositio de facturación')
    with page.expect_navigation():
        with page.expect_popup() as popup_info:
            page.click("text=Emitir Factura")
        page1 = popup_info.value
    return page1


def elegir_facturador(facturador, page1):
    facturador = facturador.upper()
    logger.info(f'Buscando boton de monotributista para el cual tributar con nombre {facturador}')
    page1.click(f"input[role=\"button\"]:has-text(\"{facturador}\")")


def generar_factura(config, page1):
    page1.click("a[role=\"button\"]:has-text(\"Generar Comprobantes\")")
    logger.info('Eligiendo punto de venta y tipo de factura')
    page1.select_option("select[name=\"puntoDeVenta\"]", str(config.punto_de_venta))
    # Wait it automatically selects Factura C on second dropdown menu
    time.sleep(2)

    page1.click("text=Continuar >")
    logger.info('Ingresando servicio como tipo de facturacion')
    # Facturacion de Servicios
    servicios = "2"
    page1.select_option("select[name=\"idConcepto\"]", servicios)

    # Completamos la fecha de la factura. Normalmente va a ser la del dia de 'hoy' y no haria falta
    # Pero tambien puede ser la de 10 dias antes (limite de facturacion retroactiva de servicios)
    # Entonces la llenamos siempre, incluso si ya esta en el valor deseado.
    date_str = config.date.strftime('%d/%m/%Y')
    page1.fill("input[name=\"periodoFacturadoDesde\"]", date_str)
    page1.fill("input[name=\"periodoFacturadoHasta\"]", date_str)
    # El dia de vencimiento tambien es input, pero siempre debe ser hoy, sino no vale facturarlo

    page1.click("text=Continuar >")
    logger.info(
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


def confirmar_factura(config, page1):
    if config.askconfirmation:
        resp = input('Presiona ENTER para facturar, o cualquier otra tecla para cancelar\n')
        if resp != '':
            logger.info('Cancelando Facturacion')
            exit(0)
    # Clickear confirmar y aceptar el popup
    page1.once("dialog", lambda dialog: dialog.accept())
    page1.click("text=Confirmar Datos...")


def descargar_factura(page1, destination):
    # Imprimir comprobante con nombre autogenerado por AFIP
    with page1.expect_download() as download_info:
        page1.click("text=Imprimir...")
    download = download_info.value
    download.save_as(str(destination) + download.suggested_filename)
    logger.info(f"File saved @ {download.suggested_filename}")


def validate_facturacion_config(config: FacturacionParameters, allow_billing_past_invoices: bool):
    today = datetime.datetime.today().date()
    if config.service_amount > LIMITE_FACTURACION_ANONIMA and not config.cuit_receptor:
        raise ValueError(f'Para facturar {config.service_amount} se requiere CUIT de consumidor final')

    if config.date > today:
        raise ValueError(f"No se puede emitir facturas para el futuro. "
                         f"Hoy es {today}, per la factura es para el {config.date}")
    if allow_billing_past_invoices is False and config.date < today:
        raise ValueError("No se puede facturar para días anteriores si no se especifica --allow-billing-past-invoices")

    if (today - config.date) > datetime.timedelta(days=10):
        raise ValueError("No se puede facturar servicios realizados hace mas de 10 dias")

    return today


def validate_we_dont_repeat_any_invoice(configs: List[FacturacionParameters]):
    """Perhaps delegate logic into class??"""
    with open(invoicespath, 'r') as f:
        oldfacturas = json.load(f)

    for config in configs:
        if config.to_dict() in oldfacturas:
            raise ValueError(f"{config} was already billed. Aborting because we can't allow double billing")


def mark_invoices_as_already_billed(configs: List[FacturacionParameters]):
    """We arbitrarily assume one can idenitify an invoice univocally by cuil, date, service, monto and cuit dest"""
    with open(invoicespath, 'r') as f:
        oldfacturas = json.load(f)

    newfacturas = [x.to_dict() for x in configs]
    oldfacturas.extend(newfacturas)
    with open(invoicespath, 'w') as f:
        json.dump(oldfacturas, f, indent=2, ensure_ascii=False, sort_keys=True)


def repeat_facturacion(page1, facturaciones_por_dia, destination):
    for config in facturaciones_por_dia:
        logger.info(f'Generating invoice: {config}')
        generar_factura(config, page1)
        logger.info("Confirming factura")
        confirmar_factura(config, page1)
        logger.info("Downloading factura")
        descargar_factura(page1, destination)

        # Go back to main menu and start with the next invoice/factura
        logger.info("Returning to main menu to generate next invoice")
        page1.click("text=Menú Principal")
        logger.info('Sleeping to simulate human behaviour')
        time.sleep(5)

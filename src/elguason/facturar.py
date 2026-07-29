import datetime
import json
from dataclasses import dataclass
import time
from pathlib import Path
from typing import List

from loguru import logger
from playwright.sync_api import sync_playwright

from elguason import random_user_agent


@dataclass
class FacturacionParameters:
    cuil: str
    password: str
    facturador: str
    service_name: str
    service_amount: int
    cuit_receptor: str
    punto_de_venta: str
    askconfirmation: bool = True
    date_from: datetime.date = None
    date_to: datetime.date = None
    date_payment: datetime.date = None
    date: datetime.date = datetime.datetime.today().date()
    # Cantidad de unidades a facturar (ej: cantidad de sesiones). Por defecto 1.
    service_units: int = 1
    # Medio de pago informado en la factura (ej: "Contado", "Tarjeta de débito").
    # Si es None se usa el flujo por defecto (checkbox "Contado").
    payment_method: str = None
    # Código de actividad del facturador. Para psicología es "04".
    actividad: str = None

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



def facturar_sol(
        cuil,
        password,
        facturador,
        facturaciones: List[FacturacionParameters],
        allow_billing_past_invoices: bool,
        destination: str,
):
    """Flujo de facturación para la psicóloga (Factura C, actividad 04).

    Es análogo a ``facturar_multiples`` pero usa ``generar_factura_sol``, que
    contempla los pasos específicos del rubro psicología:

        - Elegir la actividad como psicóloga (número 04)
        - Servicio de "Tratamiento"
        - Consumidor final con CUIT del paciente
        - Medio de pago tomado del Excel
        - Cantidad de unidades (sesiones) y honorarios por unidad
    """
    # Validate
    validate_we_dont_repeat_any_invoice(facturaciones)
    for facturacion_config in facturaciones:
        validate_facturacion_config(facturacion_config, allow_billing_past_invoices)

    # Execute
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=1000)
        logger.info("Inicio de facturacion a pacientes (psicóloga) 📝")
        context = browser.new_context(accept_downloads=True, user_agent=random_user_agent())
        logger.info("Login into AFIP")
        page = login(cuil=cuil, password=password, context=context)
        logger.info("Ingresando a Comprobantes en línea")
        page1 = enter_facturacion_microsite(page=page)
        logger.info(f"Eligiendo facturador por nombre={facturador}")
        elegir_facturador(facturador=facturador, page1=page1)
        logger.info("Comenzando a generar comprobantes")
        repeat_facturacion_sol(page1=page1, facturaciones=facturaciones, destination=destination)
        context.close()
        logger.info("Facturaciones a pacientes finalizadas ✨")
        browser.close()

    mark_invoices_as_already_billed(configs=facturaciones)


def repeat_facturacion_sol(page1, facturaciones, destination):
    for config in facturaciones:
        logger.info(f'Generando comprobante: {config}')
        generar_factura_sol(config=config, page1=page1)
        logger.info("Confirmando factura")
        confirmar_factura(config=config, page1=page1)
        logger.info("Descargando factura")
        descargar_factura(page1=page1, destination=destination)

        # Volver al menú principal para la próxima factura
        logger.info("Volviendo al menú principal para el próximo comprobante")
        page1.click("text=Menú Principal")
        logger.info('Sleeping to simulate human behaviour')
        time.sleep(5)


def generar_factura_sol(config: FacturacionParameters, page1):
    """Genera un comprobante siguiendo el flujo específico de la psicóloga.

    Pasos (según pedido):
        3. Generar comprobante
        4. Punto de Venta a utilizar
        5. Factura C
        6. Fecha del comprobante
        7. Servicio de "Tratamiento"
        8. Consumidor final
        9. CUIT del paciente
        10. Medio de pago (del Excel)
        11. Cantidad de unidades y honorarios (del Excel)
        12. Continuar / confirmar
    """
    # 3. Generar comprobante
    page1.click("a[role=\"button\"]:has-text(\"Generar Comprobantes\")")

    logger.info('Eligiendo punto de venta y tipo de factura (Factura C)')

    # 4. Punto de Venta a utilizar
    page1.select_option("select[name=\"puntoDeVenta\"]", config.punto_de_venta)

    # 5. Factura C: se autoselecciona en el segundo dropdown al elegir punto de venta
    time.sleep(2)
    page1.click("text=Continuar >")

    # 6. Fecha del comprobante / período facturado
    if config.date_from is not None and config.date_to is not None:
        date_from = config.date_from.strftime('%d/%m/%Y')
        date_to = config.date_to.strftime('%d/%m/%Y')
        date_payment = config.date_payment.strftime('%d/%m/%Y')
    else:
        date_from = date_to = date_payment = config.date.strftime('%d/%m/%Y')

    page1.fill("input[name=\"periodoFacturadoDesde\"]", date_from)
    page1.fill("input[name=\"periodoFacturadoHasta\"]", date_to)
    page1.fill("input[name=\"vencimientoPago\"]", date_payment)
    page1.click("text=Continuar >")


    # 7. Servicio de tratamiento -> concepto "Servicios"
    logger.info('Ingresando concepto: Servicios')
    servicios = "2"
    page1.select_option("select[name=\"idConcepto\"]", servicios)

    # 8. Consumidor final
    logger.info('Receptor: consumidor final')
    consumidor_final = "5"
    page1.select_option("select[name=\"idIVAReceptor\"]", consumidor_final)

    # 9. CUIT del paciente
    if config.cuit_receptor:
        page1.click("input[name=\"nroDocReceptor\"]")
        page1.fill("input[name=\"nroDocReceptor\"]", config.cuit_receptor)

    # 10. Medio de pago (del Excel)
    if config.payment_method:
        # TODO: Mapear el medio de pago del Excel (ej: "Contado", "Tarjeta de débito",
        #  "Transferencia") al control correcto de la web. Se desconoce si es un
        #  <select> (con qué `name`/`value`) o un checkbox distinto al de "Contado".
        #  Mientras no se verifique en la web real, no completar el medio de pago
        #  arbitrario y caer al comportamiento por defecto (Contado) para no romper.
        logger.warning(
            f"Medio de pago '{config.payment_method}' aún no soportado; "
            f"se marca 'Contado' por defecto (revisar TODO)."
        )
        page1.check("input[name=\"formaDePago\"]")
    else:
        # Comportamiento por defecto: Contado
        page1.check("input[name=\"formaDePago\"]")
    page1.click("text=Continuar >")

    # 7 (detalle). Descripción del servicio: Tratamiento
    page1.click("textarea[name=\"detalleDescripcion\"]")
    page1.fill("textarea[name=\"detalleDescripcion\"]", config.service_name)

    # 11. Cantidad de unidades (sesiones) y honorarios por unidad
    # TODO: Verificar el `name` real del input de cantidad de unidades en la web
    #  (probablemente algo como `input[name="detalleCantidad"]`). Además, confirmar
    #  si `detallePrecio` espera el precio unitario (honorarios por sesión) o el total.
    #  Si espera el unitario, usar `honorarios_por_sesion` en vez del total.
    # page1.click("input[name=\"detalleCantidad\"]")
    # page1.fill("input[name=\"detalleCantidad\"]", str(config.service_units))
    page1.click("input[name=\"detallePrecio\"]")
    page1.fill("input[name=\"detallePrecio\"]", str(config.service_amount))

    # 12. Continuar (luego confirmar_factura hace "Confirmar Datos")
    page1.click("text=Continuar >")



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
    filename = str(destination) + download.suggested_filename
    download.save_as(filename)
    logger.info(f"File saved @ {filename}")


def validate_facturacion_config(config: FacturacionParameters, allow_billing_past_invoices: bool):
    today = datetime.datetime.today().date()
    if config.service_amount > LIMITE_FACTURACION_ANONIMA and not config.cuit_receptor:
        raise ValueError(f'Para facturar {config.service_amount} se requiere CUIT de consumidor final')

    if config.date > today:
        raise ValueError(f"No se puede emitir facturas para el futuro. "
                         f"Hoy es {today}, pero la factura es para el {config.date}")
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

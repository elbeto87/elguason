import os
from dataclasses import dataclass
import time
from dotenv import load_dotenv

from playwright.sync_api import Playwright, sync_playwright


@dataclass
class FacturacionParameters:
    cuil: str
    password: str
    facturador_name: str
    service_name: str
    punto_de_venta: int
    service_amount: int


def run(
    plwright: Playwright,
    config: FacturacionParameters,
    dry_run=True,
) -> None:
    if config.service_amount > 12500:
        raise ValueError(f'No esta soportado facturar mas de {config.service_amount}, '
                         f'pues requiere CUIL de consumidor final')

    browser = plwright.chromium.launch(headless=False, slow_mo=2000)
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

    # with page.expect_navigation(url="https://monotributo.afip.gob.ar/app/Inicio.aspx"):
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
    # assert page1.url == "https://serviciosjava2.afip.gob.ar/rcel/jsp/menu_ppal.jsp"
    # Click a[role="button"]:has-text("Generar Comprobantes")
    page1.click("a[role=\"button\"]:has-text(\"Generar Comprobantes\")")
    # assert page1.url == "https://serviciosjava2.afip.gob.ar/rcel/jsp/buscarPtosVtas.do"

    print('Eligiendo punto de venta y tipo de factura')
    # Modificar si hay mas de un punto de venta

    page1.select_option("select[name=\"puntoDeVenta\"]", str(config.punto_de_venta))

    # Wait it automatically selects Factura C on second dropdown menu
    time.sleep(2)
    page1.click("text=Continuar >")

    print('Ingresando servicio como tipo de facturacion')
    # Facturacion de Servicios
    servicios = "2"
    page1.select_option("select[name=\"idConcepto\"]", servicios)
    # Click text=Continuar >
    page1.click("text=Continuar >")
    # assert page1.url == "https://serviciosjava2.afip.gob.ar/rcel/jsp/genComDatosReceptor.do"

    print(
        f'Facturando {config.service_name} por un monto de {config.service_amount} '
        f'para consumidor final con pago al contado'
    )
    consumidor_final = 5
    page1.select_option("select[name=\"idIVAReceptor\"]", f"{consumidor_final}")

    # Check input[name="formaDePago"]
    # Chequear Checkbox de Contado
    page1.check("input[name=\"formaDePago\"]")
    page1.click("text=Continuar >")

    page1.click("textarea[name=\"detalleDescripcion\"]")
    page1.fill("textarea[name=\"detalleDescripcion\"]", f"{config.service_name}")

    page1.click("input[name=\"detallePrecio\"]")
    page1.fill("input[name=\"detallePrecio\"]", f"{config.service_amount}")

    page1.click("text=Continuar >")

    if dry_run:
        print('Operacion exitosa, pero evitamos la facturacion pues dry_run=True')
        print('Presiona ENTER para salir')
        input()
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


load_dotenv()

monto = int(input('Ingresa el monto a facturar [10.000]: ') or 10_000)
servicio = input('Ingresa el titulo del servicio a facturar [Servicios Profesionales]: ')
dry_run = input('Queres facturar posta o solo ver si funciona? Presiona Y va a facturar,'
                'Cualquier otra tecla para demo: ')

config = FacturacionParameters(
    cuil=os.environ['CUIL'],
    password=os.environ['PASSWORD'],
    facturador_name=os.environ['FACTURADOR'],
    service_name=servicio or 'Servicios Profesionales',
    punto_de_venta=os.environ.get("PUNTO_DE_VENTA", 1),
    service_amount=monto
)

with sync_playwright() as playwright:
    print("Inicio de facturacion 📝")
    run(playwright, config=config, dry_run=dry_run.upper() != 'Y')
    print("Facturacion finalizada ✨")

import os
import random
from dataclasses import dataclass
from decimal import Decimal
import time

from playwright.sync_api import Playwright, sync_playwright


@dataclass
class FacturacionParameters:
    cuil: str
    password: str
    facturador_name: str
    service_name: str
    service_amount: Decimal


def run(
    plwright: Playwright,
    config: FacturacionParameters,
    dry_run=True,
) -> None:
    browser = plwright.chromium.launch(headless=False, slow_mo=2000)
    context = browser.new_context(
        accept_downloads=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    )

    page = context.new_page()
    page.goto("https://auth.afip.gov.ar/contribuyente_/login.xhtml?action=SYSTEM&system=admin_mono")

    page.fill("input[name=\"F1:username\"]", config.cuil)
    page.press("input[name=\"F1:username\"]", "Enter")
    page.fill("input[name=\"F1:password\"]", config.password)

    # with page.expect_navigation(url="https://monotributo.afip.gob.ar/app/Inicio.aspx"):
    with page.expect_navigation():
        page.press("input[name=\"F1:password\"]", "Enter")

    # Click text=Emitir Factura
    with page.expect_navigation():
        with page.expect_popup() as popup_info:
            page.click("text=Emitir Factura")
        page1 = popup_info.value

    # Click input[role="button"]:has-text("APELLIDO NOMBRE1 NOMBRE2") # Validar contra sitio web real
    facturador = config.facturador_name.upper()
    page1.click(f"input[role=\"button\"]:has-text(\"{facturador}\")")
    # assert page1.url == "https://serviciosjava2.afip.gob.ar/rcel/jsp/menu_ppal.jsp"
    # Click a[role="button"]:has-text("Generar Comprobantes")
    page1.click("a[role=\"button\"]:has-text(\"Generar Comprobantes\")")
    # assert page1.url == "https://serviciosjava2.afip.gob.ar/rcel/jsp/buscarPtosVtas.do"
    # Select 1
    # Modificar si hay mas de un punto de venta
    page1.select_option("select[name=\"puntoDeVenta\"]", "1")
    # Wait it automatically selects Factura C on second dropdown menu
    time.sleep(2)
    page1.click("text=Continuar >")

    # Facturacion de Servicios
    servicios = 2
    page1.select_option("select[name=\"idConcepto\"]", f"{servicios}")
    # Click text=Continuar >
    page1.click("text=Continuar >")
    # assert page1.url == "https://serviciosjava2.afip.gob.ar/rcel/jsp/genComDatosReceptor.do"
    # Select 5
    consumidor_final = 5
    page1.select_option("select[name=\"idIVAReceptor\"]", f"{consumidor_final}")

    # Check input[name="formaDePago"]
    # Chequear Contado
    page1.check("input[name=\"formaDePago\"]")
    # Click text=Continuar >
    page1.click("text=Continuar >")
    # assert page1.url == "https://serviciosjava2.afip.gob.ar/rcel/jsp/genComDatosOperacion.do"
    # Click textarea[name="detalleDescripcion"]
    page1.click("textarea[name=\"detalleDescripcion\"]")
    # Fill textarea[name="detalleDescripcion"]
    page1.fill("textarea[name=\"detalleDescripcion\"]", f"{config.service_name}")
    # Click input[name="detallePrecio"]
    page1.click("input[name=\"detallePrecio\"]")
    # Fill input[name="detallePrecio"]
    page1.fill("input[name=\"detallePrecio\"]", f"{config.service_amount}")

    # Click text=Continuar >
    page1.click("text=Continuar >")
    # assert page1.url == "https://serviciosjava2.afip.gob.ar/rcel/jsp/genComResumenDatos.do"

    if dry_run:
        print('Operacion exitosa, pero evitamos la facturacion pues dry_run=True')
        print('Presiona ENTER para salir')
        input()
        exit(0)

    # Click text=Confirmar Datos...
    page1.once("dialog", lambda dialog: dialog.dismiss())
    page1.click("text=Confirmar Datos...")

    # # Click text=Imprimir...
    # with page1.expect_download() as download_info:
    #     page1.click("text=Imprimir...")
    # download = download_info.value
    # print(repr(download))
    # print(download.path())

    context.close()
    browser.close()


config = FacturacionParameters(
    cuil=os.environ['CUIL'],
    password=os.environ['PASSWORD'],
    facturador_name=os.environ['FACTURADOR'],
    service_name='Consulta',
    service_amount=Decimal(random.choice([12100, 11300, 10200, 8900, 5600, 9000]))
)

with sync_playwright() as playwright:
    run(playwright, config=config)

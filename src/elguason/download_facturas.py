import os

from dotenv import load_dotenv
from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False, slow_mo=1000)
    context = browser.new_context(accept_downloads=True)

    page = context.new_page()
    page.goto("https://auth.afip.gov.ar/contribuyente_/login.xhtml?action=SYSTEM&system=admin_mono")
    page.fill("input[name=\"F1:username\"]", os.getenv('CUIL'))
    page.press("input[name=\"F1:username\"]", "Enter")
    page.fill("input[name=\"F1:password\"]", os.getenv('PASSWORD'))

    with page.expect_navigation():
        page.press("input[name=\"F1:password\"]", "Enter")

    with page.expect_navigation():
        with page.expect_popup() as popup_info:
            page.click("text=Facturas Emitidas")
        page1 = popup_info.value

    page1.click("input[role=\"button\"]:has-text(\"AMBROSINI RODRIGO NAHUEL\")")
    page1.click("a[role=\"button\"]:has-text(\"Consultas\")")

    page1.fill("input[name=\"fechaEmisionDesde\"]", "01/10/2021")
    page1.fill("input[name=\"fechaEmisionHasta\"]", "31/10/2021")
    page1.click("text=Buscar")

    all_ver_buttons = page1.query_selector_all("input[value=Ver]")
    for button in all_ver_buttons:
        with page1.expect_download() as download_info:
            button.click()

        download = download_info.value
        download.save_as(download.suggested_filename)
        import time; time.sleep(1)

    context.close()
    browser.close()


with sync_playwright() as playwright:
    load_dotenv()
    run(playwright)

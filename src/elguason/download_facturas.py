import datetime
from dataclasses import dataclass

from playwright.sync_api import Playwright, sync_playwright


@dataclass
class DownloadComprobantesConfig:
    cuil: str
    password: str
    facturador_name: str
    start_date: datetime.date
    end_date: datetime.date
    download_folder: str
    askconfirmation: bool = True


def run_download(
    playright: Playwright,
    config: DownloadComprobantesConfig,
) -> str:
    browser = playright.chromium.launch(headless=False, slow_mo=1000)
    context = browser.new_context(accept_downloads=True)

    today = datetime.datetime.today().date()
    if config.end_date > today:
        raise ValueError('No se pueden descargar comprobantes del futuro')
    if config.start_date.month != config.end_date.month:
        raise ValueError('La fecha desde hasta debe pertenecer al mismo mes')

    page = context.new_page()

    # Login
    page.goto("https://auth.afip.gov.ar/contribuyente_/login.xhtml?action=SYSTEM&system=admin_mono")
    page.fill("input[name=\"F1:username\"]", config.cuil)
    page.press("input[name=\"F1:username\"]", "Enter")
    page.fill("input[name=\"F1:password\"]", config.password)
    with page.expect_navigation():
        page.press("input[name=\"F1:password\"]", "Enter")

    # Go to emitir facturas microsite
    with page.expect_navigation():
        with page.expect_popup() as popup_info:
            page.click("text=Facturas Emitidas")
        page1 = popup_info.value

    # Click on facturador button
    page1.click(f"input[role=\"button\"]:has-text(\"{config.facturador_name}\")")

    # Click on consultas section
    page1.click("a[role=\"button\"]:has-text(\"Consultas\")")

    # Edit start and end date of the invoices report
    page1.fill("input[name=\"fechaEmisionDesde\"]", config.start_date.strftime('%d/%m/%Y'))
    page1.fill("input[name=\"fechaEmisionHasta\"]", config.end_date.strftime('%d/%m/%Y'))
    page1.click("text=Buscar")

    # Find all download buttons, they all are buttons with Ver value.
    all_ver_buttons = page1.query_selector_all("input[value=Ver]")

    # Click all download buttons, waiting a few miliseconds to emulate user behaviour
    for button in all_ver_buttons:
        with page1.expect_download() as download_info:
            button.click()

        download = download_info.value
        download.save_as(config.download_folder + '/' + download.suggested_filename)
        import time; time.sleep(1)

    context.close()
    browser.close()
    return config.download_folder


def download_comprobantes(config: DownloadComprobantesConfig) -> str:
    with sync_playwright() as playwright:
        return run_download(playwright, config=config)

import datetime
from dataclasses import dataclass

from loguru import logger
from playwright.sync_api import Playwright, sync_playwright

from elguason import random_user_agent


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
    context = browser.new_context(accept_downloads=True, user_agent=random_user_agent())

    logger.info("Validating config")
    today = datetime.datetime.today().date()
    if config.end_date > today:
        raise ValueError('No se pueden descargar comprobantes del futuro')

    page = context.new_page()

    # Login
    logger.info("Login into AFIP")
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

    # After clicking Emitir Facturas, a redirect opens a new page that requires creds again
    page1.fill("input[name=\"F1:username\"]", config.cuil)
    page1.press("input[name=\"F1:username\"]", "Enter")
    page1.fill("input[name=\"F1:password\"]", config.password)
    page1.press("input[name=\"F1:password\"]", "Enter")
    
    # Click on facturador button
    page1.click(f"input[role=\"button\"]:has-text(\"{config.facturador_name}\")")

    logger.info("Clicking consultas")
    # Click on consultas section
    page1.click("a[role=\"button\"]:has-text(\"Consultas\")")

    logger.info("Entering date range for invoices")
    # Edit start and end date of the invoices report
    page1.fill("input[name=\"fechaEmisionDesde\"]", config.start_date.strftime('%d/%m/%Y'))
    page1.fill("input[name=\"fechaEmisionHasta\"]", config.end_date.strftime('%d/%m/%Y'))
    page1.click("text=Buscar")

    # Find all download buttons, they all are buttons with Ver value.
    all_ver_buttons = page1.query_selector_all("input[value=Ver]")

    logger.info("Downloading invoices")
    # Click all download buttons, waiting a few miliseconds to emulate user behaviour
    for button in all_ver_buttons:
        with page1.expect_download() as download_info:
            button.click()

        download = download_info.value
        if not download:
            logger.error(f"Failed to download {download_info}")
            continue

        savepath = config.download_folder + '/' + download.suggested_filename
        logger.info(f"Saving invoice into {savepath}")
        download.save_as(savepath)
        import time; time.sleep(1)

    context.close()
    browser.close()
    return config.download_folder


def download_comprobantes(config: DownloadComprobantesConfig) -> str:
    with sync_playwright() as playwright:
        return run_download(playwright, config=config)

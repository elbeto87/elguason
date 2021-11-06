import sys
from pathlib import Path

from crontab import CronTab
from loguru import logger


ENTRYPOINT = 'facturarcsv'
entrypoints_path = Path(sys.executable).parent
facturarcsvbin = str(entrypoints_path / ENTRYPOINT)


def remove_crons():
    logger.info("Removing old crons")
    # Remove all crons that use the facturarcsv binary entrypoint
    with CronTab(user=True) as cron:
        existing_jobs = [x for x in cron.find_command(facturarcsvbin)]
        for job in existing_jobs:
            logger.debug(f"Removing {job.cron!s}")
            cron.remove(job)


def configure(hour, spec, outputpath, bill_old_invoices):
    # Remove previous configs
    remove_crons()

    logger.info("Configuring new cron")
    # Create new one
    if bill_old_invoices:
        new_command = f'{facturarcsvbin} {spec} --allow-billing-past-invoices > {outputpath}'
    else:
        new_command = f'{facturarcsvbin} {spec} > {outputpath}'

    logger.info(f"Command: {new_command}")
    with CronTab(user=True) as cron:
        job = cron.new(command=new_command)
        job.setall(f'0 {hour} * * *')  # Set cron to run on hour:00 every day
        assert job.is_valid()

    cron = str(job.cron).strip()
    logger.debug(f"Cron: '{cron}'")
    return cron

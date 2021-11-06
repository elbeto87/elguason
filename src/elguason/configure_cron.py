import sys
from pathlib import Path

from crontab import CronTab
from loguru import logger

ENTRYPOINT = 'facturarcsv'
entrypoints_path = Path(sys.executable).parent
facturarcsvbin = str(entrypoints_path / ENTRYPOINT)


def remove(hour, spec, outputpath):

    new_command = f'{facturarcsvbin} {spec} > {outputpath}'
    with CronTab(user=True) as cron:
        # Find or create cron
        existing_jobs = [x for x in cron.find_command(new_command)]
        for job in existing_jobs:
            cron.remove(job)


def configure(hour, spec, outputpath, bill_old_invoices):
    if bill_old_invoices:
        new_command = f'{facturarcsvbin} {spec} --allow-billing-past-invoices > {outputpath}'
    else:
        new_command = f'{facturarcsvbin} {spec} > {outputpath}'

    with CronTab(user=True) as cron:
        # Find or create cron
        existing_job = next((x for x in cron.find_command(new_command)), None)
        if existing_job:
            logger.info("Updating existing cron")
            job = existing_job
        else:
            logger.info("Creating new cron")
            job = cron.new(command=new_command)

        job.command = new_command
        job.setall(f'0 {hour} * * *')  # Set cron to run on hour:00 minutes every day
        assert job.is_valid()

    return str(job.cron).strip()

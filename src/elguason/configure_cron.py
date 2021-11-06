import sys
from pathlib import Path

from crontab import CronTab
from loguru import logger


def configure(hour, spec, outputpath):
    entrypoints_path = Path(sys.executable).parent
    micontador = str(entrypoints_path / 'micontador')

    new_command = f'{micontador} {spec} > {outputpath}'

    with CronTab(user=True) as cron:
        # Find or create cron
        existing_job = next((x for x in cron.find_command(micontador)), None)
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

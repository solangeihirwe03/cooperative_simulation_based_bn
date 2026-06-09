import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.penalty_cron import apply_monthly_penalties_job

logger = logging.getLogger("penalty_scheduler")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

scheduler = AsyncIOScheduler()

def setup_scheduler():
    logger.info("Initializing and starting APScheduler...")
    
    # Run every 24 hours — evaluates each loan's own 30-day rolling windows
    trigger = IntervalTrigger(hours=24)
    
    scheduler.add_job(
        apply_monthly_penalties_job,
        trigger=trigger,
        id="apply_penalty_job",
        name="Daily check: penalize loans with missed 30-day repayment windows",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("APScheduler started. Penalty evaluation runs every 24 hours.")

def shutdown_scheduler():
    logger.info("Shutting down APScheduler...")
    scheduler.shutdown()
    logger.info("APScheduler shut down.")

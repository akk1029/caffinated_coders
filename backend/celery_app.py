from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery = Celery("pantrypet", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery.conf.beat_schedule = {
    "decay-pet-health-midnight": {
        "task": "app.tasks.decay_pet_health",
        "schedule": crontab(hour=0, minute=0),
    },
    "reset-recipe-counts-midnight": {
        "task": "app.tasks.reset_daily_counts",
        "schedule": crontab(hour=0, minute=1),
    },
    "expire-subscriptions-midnight": {
        "task": "app.tasks.expire_lapsed_subscriptions",
        "schedule": crontab(hour=0, minute=2),
    },
}

celery.autodiscover_tasks(["app"])

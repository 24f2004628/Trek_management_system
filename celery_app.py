from celery import Celery
from celery.schedules import crontab


celery = Celery(
    "trek_app",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["tasks"]
)


celery.conf.beat_schedule = {

    "daily-trek-reminders": {

        "task": "tasks.daily_trek_reminders",
        "schedule": crontab(
            hour=9,
            minute=0
        )

    },

    "monthly-activity-report": {

        "task": "tasks.monthly_activity_report",

        "schedule": crontab(
            day_of_month=1,
            hour=9,
            minute=0
        )

    }

}
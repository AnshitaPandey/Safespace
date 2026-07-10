from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "safespace",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.memory_extraction",
        "app.workers.journal_summarization",
        "app.workers.analytics_rollup",
        "app.workers.message_tagging",
        "app.workers.quality_scoring",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Weekly/monthly report generation, run on a schedule rather than triggered per-request.
celery_app.conf.beat_schedule = {
    "generate-weekly-reports": {
        "task": "app.workers.analytics_rollup.generate_all_weekly_reports",
        "schedule": 60 * 60 * 24,  # check daily; task itself only acts on the right day
    },
}

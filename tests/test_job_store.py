from datetime import datetime, timezone

from app.models.job import TestJob
from app.services.job_store import JobStore


def test_job_persists_between_store_instances(
    tmp_path,
):
    database_path = tmp_path / "jobs.db"

    first_store = JobStore(
        database_path=str(database_path)
    )

    now = datetime.now(timezone.utc)

    job = TestJob(
        job_id="persistent123",
        status="running",
        page_url="https://example.com",
        objective="Test the homepage",
        headless=True,
        created_at=now,
        updated_at=now,
    )

    first_store.create(job)

    second_store = JobStore(
        database_path=str(database_path)
    )

    saved_job = second_store.get(
        "persistent123"
    )

    assert saved_job is not None
    assert saved_job.job_id == "persistent123"
    assert saved_job.status == "running"
    assert saved_job.page_url == "https://example.com"


def test_job_result_can_be_updated(
    tmp_path,
):
    database_path = tmp_path / "jobs.db"

    store = JobStore(
        database_path=str(database_path)
    )

    now = datetime.now(timezone.utc)

    job = TestJob(
        job_id="completed123",
        status="queued",
        page_url="https://example.com",
        objective="Test the homepage",
        headless=True,
        created_at=now,
        updated_at=now,
    )

    store.create(job)

    job.status = "completed"
    job.result = {
        "inspection": {},
        "test_plan": {},
        "runs": [],
    }

    store.update(job)

    saved_job = store.get("completed123")

    assert saved_job is not None
    assert saved_job.status == "completed"
    assert saved_job.result is not None
    assert saved_job.result["runs"] == []
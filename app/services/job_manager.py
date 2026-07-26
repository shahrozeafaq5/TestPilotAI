from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
)
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from playwright.sync_api import sync_playwright

from app.models.job import JobStatus, TestJob
from app.services.job_store import JobStore
from app.services.test_orchestrator import (
    TestOrchestrator,
)


def current_utc_time() -> datetime:
    return datetime.now(timezone.utc)


class TestJobManager:
    def __init__(
        self,
        orchestrator: TestOrchestrator,
        job_store: JobStore,
        max_workers: int = 1,
    ) -> None:
        self.orchestrator = orchestrator
        self.job_store = job_store
        self.lock = Lock()

        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="testpilot-worker",
        )

        self.futures: dict[
            str,
            Future[None],
        ] = {}

    def submit(
        self,
        page_url: str,
        objective: str,
        headless: bool,
    ) -> TestJob:
        job_id = uuid4().hex[:12]
        now = current_utc_time()

        job = TestJob(
            job_id=job_id,
            status="queued",
            page_url=page_url,
            objective=objective,
            headless=headless,
            created_at=now,
            updated_at=now,
        )

        with self.lock:
            self.job_store.create(job)

        future = self.executor.submit(
            self._execute_job,
            job_id,
            page_url,
            objective,
            headless,
        )

        with self.lock:
            self.futures[job_id] = future

        future.add_done_callback(
            lambda _future: self._forget_future(
                job_id
            )
        )

        return job.model_copy(deep=True)

    def get(
        self,
        job_id: str,
    ) -> TestJob | None:
        with self.lock:
            job = self.job_store.get(job_id)

        if job is None:
            return None

        return job.model_copy(deep=True)

    def list_recent(
        self,
        limit: int = 20,
        status: JobStatus | None = None,
    ) -> list[TestJob]:
        with self.lock:
            jobs = self.job_store.list_recent(
                limit=limit,
                status=status,
            )

        return [
            job.model_copy(deep=True)
            for job in jobs
        ]

    def cancel(
        self,
        job_id: str,
    ) -> TestJob | None:
        with self.lock:
            job = self.job_store.get(job_id)
            future = self.futures.get(job_id)

        if job is None:
            return None

        if job.status == "cancelled":
            return job.model_copy(deep=True)

        if job.status != "queued":
            raise ValueError(
                "Only queued jobs can be cancelled. "
                f"Current status is '{job.status}'."
            )

        if future is None or not future.cancel():
            current_job = self.get(job_id)

            current_status = (
                current_job.status
                if current_job is not None
                else "unknown"
            )

            raise ValueError(
                "The job has already started and can "
                "no longer be cancelled. "
                f"Current status is '{current_status}'."
            )

        with self.lock:
            updated_job = self.job_store.get(job_id)

            if updated_job is None:
                return None

            updated_job.status = "cancelled"
            updated_job.updated_at = (
                current_utc_time()
            )
            updated_job.result = None
            updated_job.error = (
                "Job was cancelled before execution."
            )

            self.job_store.update(updated_job)

        return updated_job.model_copy(deep=True)

    def delete(
        self,
        job_id: str,
    ) -> bool:
        with self.lock:
            job = self.job_store.get(job_id)

            if job is None:
                return False

            if job.status in {
                "queued",
                "running",
            }:
                raise ValueError(
                    "Queued or running jobs cannot "
                    "be deleted. Cancel or wait for "
                    "the job to finish first."
                )

            return self.job_store.delete(job_id)

    def shutdown(self) -> None:
        self.executor.shutdown(
            wait=False,
            cancel_futures=True,
        )

    def _execute_job(
        self,
        job_id: str,
        page_url: str,
        objective: str,
        headless: bool,
    ) -> None:
        self._update_job(
            job_id=job_id,
            status="running",
        )

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=headless
                )

                try:
                    workflow_result = (
                        self.orchestrator.run(
                            browser=browser,
                            page_url=page_url,
                            objective=objective,
                        )
                    )

                finally:
                    browser.close()

            self._update_job(
                job_id=job_id,
                status="completed",
                result=workflow_result.model_dump(
                    mode="json"
                ),
                error=None,
            )

        except Exception as error:
            self._update_job(
                job_id=job_id,
                status="failed",
                error=str(error),
            )

    def _update_job(
        self,
        job_id: str,
        status: JobStatus,
        result: dict | None = None,
        error: str | None = None,
    ) -> None:
        with self.lock:
            job = self.job_store.get(job_id)

            if job is None:
                return

            job.status = status
            job.updated_at = current_utc_time()
            job.result = result
            job.error = error

            self.job_store.update(job)

    def _forget_future(
        self,
        job_id: str,
    ) -> None:
        with self.lock:
            self.futures.pop(job_id, None)
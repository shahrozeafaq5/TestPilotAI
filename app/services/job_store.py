import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.job import JobStatus, TestJob


class JobStore:
    def __init__(
        self,
        database_path: str = "data/testpilot.db",
    ) -> None:
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

    def create(
        self,
        job: TestJob,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO test_jobs (
                    job_id,
                    status,
                    page_url,
                    objective,
                    headless,
                    created_at,
                    updated_at,
                    result_json,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.status,
                    job.page_url,
                    job.objective,
                    int(job.headless),
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    self._serialize_result(job.result),
                    job.error,
                ),
            )

            connection.commit()

    def update(
        self,
        job: TestJob,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE test_jobs
                SET
                    status = ?,
                    page_url = ?,
                    objective = ?,
                    headless = ?,
                    updated_at = ?,
                    result_json = ?,
                    error = ?
                WHERE job_id = ?
                """,
                (
                    job.status,
                    job.page_url,
                    job.objective,
                    int(job.headless),
                    job.updated_at.isoformat(),
                    self._serialize_result(job.result),
                    job.error,
                    job.job_id,
                ),
            )

            connection.commit()

    def get(
        self,
        job_id: str,
    ) -> TestJob | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    job_id,
                    status,
                    page_url,
                    objective,
                    headless,
                    created_at,
                    updated_at,
                    result_json,
                    error
                FROM test_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def list_recent(
        self,
        limit: int = 20,
        status: JobStatus | None = None,
    ) -> list[TestJob]:
        query = """
            SELECT
                job_id,
                status,
                page_url,
                objective,
                headless,
                created_at,
                updated_at,
                result_json,
                error
            FROM test_jobs
        """

        parameters: list[object] = []

        if status is not None:
            query += " WHERE status = ?"
            parameters.append(status)

        query += " ORDER BY created_at DESC LIMIT ?"
        parameters.append(limit)

        with self._connect() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).fetchall()

        return [
            self._row_to_job(row)
            for row in rows
        ]

    def delete(
        self,
        job_id: str,
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM test_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            )

            connection.commit()

        return cursor.rowcount > 0

    def mark_incomplete_as_failed(self) -> int:
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE test_jobs
                SET
                    status = 'failed',
                    updated_at = ?,
                    error = ?
                WHERE status IN ('queued', 'running')
                """,
                (
                    now,
                    (
                        "Server restarted before "
                        "the job completed."
                    ),
                ),
            )

            connection.commit()

        return cursor.rowcount

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS test_jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    page_url TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    headless INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                index_test_jobs_status
                ON test_jobs(status)
                """
            )

            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _row_to_job(
        self,
        row: sqlite3.Row,
    ) -> TestJob:
        result = None

        if row["result_json"]:
            result = json.loads(
                row["result_json"]
            )

        return TestJob(
            job_id=row["job_id"],
            status=row["status"],
            page_url=row["page_url"],
            objective=row["objective"],
            headless=bool(row["headless"]),
            created_at=datetime.fromisoformat(
                row["created_at"]
            ),
            updated_at=datetime.fromisoformat(
                row["updated_at"]
            ),
            result=result,
            error=row["error"],
        )

    def _serialize_result(
        self,
        result: dict[str, Any] | None,
    ) -> str | None:
        if result is None:
            return None

        return json.dumps(
            result,
            ensure_ascii=False,
        )
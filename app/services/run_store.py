import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.bug_report import BugReport
from app.models.run_record import (
    StoredDiagnostics,
    StoredTestRun,
    StoredTestStep,
)
from app.services.test_orchestrator import (
    WorkflowResult,
)


class RunStore:
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

    def save_workflow(
        self,
        job_id: str,
        workflow_result: WorkflowResult,
    ) -> None:
        """
        Save all test runs belonging to one API job.

        The complete operation uses one database
        transaction.
        """

        created_at = datetime.now(
            timezone.utc
        ).isoformat()

        with self._connect() as connection:
            for workflow_run in workflow_result.runs:
                test_result = (
                    workflow_run.test_result
                )

                # Make this operation safe to repeat.
                # Deleting the run also removes its old
                # steps, diagnostics and bug report.
                connection.execute(
                    """
                    DELETE FROM test_runs
                    WHERE run_id = ?
                    """,
                    (test_result.run_id,),
                )

                connection.execute(
                    """
                    INSERT INTO test_runs (
                        run_id,
                        job_id,
                        test_name,
                        objective,
                        status,
                        error,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        test_result.run_id,
                        job_id,
                        test_result.test_name,
                        test_result.objective,
                        test_result.status,
                        test_result.error,
                        created_at,
                    ),
                )

                self._save_steps(
                    connection=connection,
                    run_id=test_result.run_id,
                    steps=test_result.steps,
                )

                self._save_diagnostics(
                    connection=connection,
                    run_id=test_result.run_id,
                    diagnostics=(
                        test_result.diagnostics
                    ),
                )

                if workflow_run.bug_report is not None:
                    self._save_bug_report(
                        connection=connection,
                        run_id=test_result.run_id,
                        bug_report=(
                            workflow_run.bug_report
                        ),
                    )

            connection.commit()

    def list_by_job_id(
        self,
        job_id: str,
    ) -> list[StoredTestRun]:
        with self._connect() as connection:
            run_rows = connection.execute(
                """
                SELECT
                    run_id,
                    job_id,
                    test_name,
                    objective,
                    status,
                    error,
                    created_at
                FROM test_runs
                WHERE job_id = ?
                ORDER BY created_at ASC
                """,
                (job_id,),
            ).fetchall()

            runs = [
                self._build_stored_run(
                    connection=connection,
                    row=row,
                )
                for row in run_rows
            ]

        return runs

    def get_run(
        self,
        run_id: str,
    ) -> StoredTestRun | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    run_id,
                    job_id,
                    test_name,
                    objective,
                    status,
                    error,
                    created_at
                FROM test_runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()

            if row is None:
                return None

            return self._build_stored_run(
                connection=connection,
                row=row,
            )

    def _save_steps(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        steps: list,
    ) -> None:
        for step in steps:
            connection.execute(
                """
                INSERT INTO test_steps (
                    run_id,
                    step_number,
                    description,
                    status,
                    error,
                    screenshot_path
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    step.step_number,
                    step.description,
                    step.status,
                    step.error,
                    step.screenshot,
                ),
            )

    def _save_diagnostics(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        diagnostics,
    ) -> None:
        connection.execute(
            """
            INSERT INTO test_diagnostics (
                run_id,
                console_errors_json,
                page_errors_json,
                failed_requests_json,
                http_errors_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                self._serialize(
                    diagnostics.console_errors
                ),
                self._serialize(
                    diagnostics.page_errors
                ),
                self._serialize(
                    diagnostics.failed_requests
                ),
                self._serialize(
                    diagnostics.http_errors
                ),
            ),
        )

    def _save_bug_report(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        bug_report: BugReport,
    ) -> None:
        connection.execute(
            """
            INSERT INTO bug_reports (
                run_id,
                title,
                test_name,
                severity,
                summary,
                reproduction_steps_json,
                expected_behavior,
                actual_behavior,
                evidence_json,
                likely_cause,
                recommended_fix
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bug_report.title,
                bug_report.test_name,
                bug_report.severity,
                bug_report.summary,
                self._serialize(
                    bug_report.reproduction_steps
                ),
                bug_report.expected_behavior,
                bug_report.actual_behavior,
                self._serialize(
                    bug_report.evidence
                ),
                bug_report.likely_cause,
                bug_report.recommended_fix,
            ),
        )

    def _build_stored_run(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> StoredTestRun:
        run_id = row["run_id"]

        steps = self._load_steps(
            connection=connection,
            run_id=run_id,
        )

        diagnostics = self._load_diagnostics(
            connection=connection,
            run_id=run_id,
        )

        bug_report = self._load_bug_report(
            connection=connection,
            run_id=run_id,
        )

        return StoredTestRun(
            run_id=run_id,
            job_id=row["job_id"],
            test_name=row["test_name"],
            objective=row["objective"],
            status=row["status"],
            error=row["error"],
            created_at=datetime.fromisoformat(
                row["created_at"]
            ),
            steps=steps,
            diagnostics=diagnostics,
            bug_report=bug_report,
        )

    def _load_steps(
        self,
        connection: sqlite3.Connection,
        run_id: str,
    ) -> list[StoredTestStep]:
        rows = connection.execute(
            """
            SELECT
                step_number,
                description,
                status,
                error,
                screenshot_path
            FROM test_steps
            WHERE run_id = ?
            ORDER BY step_number ASC
            """,
            (run_id,),
        ).fetchall()

        return [
            StoredTestStep(
                step_number=row["step_number"],
                description=row["description"],
                status=row["status"],
                error=row["error"],
                screenshot=(
                    row["screenshot_path"]
                ),
            )
            for row in rows
        ]

    def _load_diagnostics(
        self,
        connection: sqlite3.Connection,
        run_id: str,
    ) -> StoredDiagnostics:
        row = connection.execute(
            """
            SELECT
                console_errors_json,
                page_errors_json,
                failed_requests_json,
                http_errors_json
            FROM test_diagnostics
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        if row is None:
            return StoredDiagnostics()

        return StoredDiagnostics(
            console_errors=self._deserialize(
                row["console_errors_json"]
            ),
            page_errors=self._deserialize(
                row["page_errors_json"]
            ),
            failed_requests=self._deserialize(
                row["failed_requests_json"]
            ),
            http_errors=self._deserialize(
                row["http_errors_json"]
            ),
        )

    def _load_bug_report(
        self,
        connection: sqlite3.Connection,
        run_id: str,
    ) -> BugReport | None:
        row = connection.execute(
            """
            SELECT
                title,
                test_name,
                severity,
                summary,
                reproduction_steps_json,
                expected_behavior,
                actual_behavior,
                evidence_json,
                likely_cause,
                recommended_fix
            FROM bug_reports
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        return BugReport(
            title=row["title"],
            test_name=row["test_name"],
            severity=row["severity"],
            summary=row["summary"],
            reproduction_steps=self._deserialize(
                row["reproduction_steps_json"]
            ),
            expected_behavior=(
                row["expected_behavior"]
            ),
            actual_behavior=(
                row["actual_behavior"]
            ),
            evidence=self._deserialize(
                row["evidence_json"]
            ),
            likely_cause=row["likely_cause"],
            recommended_fix=(
                row["recommended_fix"]
            ),
        )

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS test_runs (
                    run_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL,

                    FOREIGN KEY (job_id)
                    REFERENCES test_jobs(job_id)
                    ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS
                index_test_runs_job_id
                ON test_runs(job_id);

                CREATE INDEX IF NOT EXISTS
                index_test_runs_status
                ON test_runs(status);

                CREATE TABLE IF NOT EXISTS test_steps (
                    step_id INTEGER PRIMARY KEY
                        AUTOINCREMENT,

                    run_id TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    screenshot_path TEXT,

                    UNIQUE (
                        run_id,
                        step_number
                    ),

                    FOREIGN KEY (run_id)
                    REFERENCES test_runs(run_id)
                    ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS
                test_diagnostics (
                    run_id TEXT PRIMARY KEY,

                    console_errors_json TEXT
                        NOT NULL,

                    page_errors_json TEXT
                        NOT NULL,

                    failed_requests_json TEXT
                        NOT NULL,

                    http_errors_json TEXT
                        NOT NULL,

                    FOREIGN KEY (run_id)
                    REFERENCES test_runs(run_id)
                    ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS bug_reports (
                    run_id TEXT PRIMARY KEY,

                    title TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    summary TEXT NOT NULL,

                    reproduction_steps_json TEXT
                        NOT NULL,

                    expected_behavior TEXT NOT NULL,
                    actual_behavior TEXT NOT NULL,

                    evidence_json TEXT NOT NULL,

                    likely_cause TEXT NOT NULL,
                    recommended_fix TEXT NOT NULL,

                    FOREIGN KEY (run_id)
                    REFERENCES test_runs(run_id)
                    ON DELETE CASCADE
                );
                """
            )

            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    def _serialize(
        self,
        value: Any,
    ) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
        )

    def _deserialize(
        self,
        value: str,
    ) -> Any:
        return json.loads(value)
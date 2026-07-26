from pathlib import Path

from app.browser.test_case_runner import TestCaseResult
from app.models.bug_report import BugReport


class ResultWriter:
    def __init__(
        self,
        reports_directory: str = "artifacts/runs",
    ) -> None:
        self.reports_directory = Path(
            reports_directory
        )

        self.reports_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(
        self,
        result: TestCaseResult,
    ) -> Path:
        """Backward-compatible method for saving results."""
        return self.write_result(result)

    def write_result(
        self,
        result: TestCaseResult,
    ) -> Path:
        run_directory = self._get_run_directory(
            result.run_id
        )

        report_path = run_directory / "result.json"

        report_path.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return report_path

    def write_bug_report(
        self,
        run_id: str,
        bug_report: BugReport,
    ) -> Path:
        run_directory = self._get_run_directory(
            run_id
        )

        report_path = (
            run_directory / "bug_report.json"
        )

        report_path.write_text(
            bug_report.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return report_path

    def _get_run_directory(
        self,
        run_id: str,
    ) -> Path:
        run_directory = (
            self.reports_directory / run_id
        )

        run_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return run_directory
from pathlib import Path

from app.browser.test_case_runner import TestCaseResult


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
        run_directory = (
            self.reports_directory / result.run_id
        )

        run_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path = run_directory / "result.json"

        report_path.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return report_path
from pathlib import Path

from app.models.run_record import StoredTestRun


class InvalidArtifactNameError(ValueError):
    pass


class ArtifactNotFoundError(FileNotFoundError):
    pass


class ArtifactService:
    ALLOWED_IMAGE_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    def __init__(
        self,
        runs_directory: str = "artifacts/runs",
    ) -> None:
        self.runs_directory = Path(
            runs_directory
        ).resolve()

    def get_screenshot(
        self,
        run: StoredTestRun,
        filename: str,
    ) -> Path:
        self._validate_filename(filename)

        run_directory = (
            self.runs_directory / run.run_id
        ).resolve()

        screenshot_path = (
            run_directory / filename
        ).resolve()

        # Prevent filenames such as ../../secret.txt
        # from escaping the expected run folder.
        if screenshot_path.parent != run_directory:
            raise InvalidArtifactNameError(
                "Invalid screenshot path."
            )

        referenced_screenshots = {
            Path(step.screenshot).resolve()
            for step in run.steps
            if step.screenshot is not None
        }

        # Only serve screenshots recorded in the
        # database for this specific test run.
        if screenshot_path not in referenced_screenshots:
            raise ArtifactNotFoundError(
                "Screenshot is not associated "
                "with this test run."
            )

        if (
            not screenshot_path.exists()
            or not screenshot_path.is_file()
        ):
            raise ArtifactNotFoundError(
                "Screenshot file was not found."
            )

        return screenshot_path

    def _validate_filename(
        self,
        filename: str,
    ) -> None:
        filename_path = Path(filename)

        if not filename or filename_path.name != filename:
            raise InvalidArtifactNameError(
                "Invalid screenshot filename."
            )

        if (
            filename_path.suffix.lower()
            not in self.ALLOWED_IMAGE_EXTENSIONS
        ):
            raise InvalidArtifactNameError(
                "Unsupported screenshot file type."
            )
from datetime import datetime, timezone

import pytest

from app.models.run_record import (
    StoredDiagnostics,
    StoredTestRun,
    StoredTestStep,
)
from app.services.artifact_service import (
    ArtifactNotFoundError,
    ArtifactService,
    InvalidArtifactNameError,
)


def create_stored_run(
    screenshot_path: str,
) -> StoredTestRun:
    return StoredTestRun(
        run_id="run123",
        job_id="job123",
        test_name="Screenshot test",
        objective="Verify screenshot retrieval",
        status="passed",
        error=None,
        created_at=datetime.now(timezone.utc),
        steps=[
            StoredTestStep(
                step_number=1,
                description="Capture screenshot",
                status="passed",
                error=None,
                screenshot=screenshot_path,
            )
        ],
        diagnostics=StoredDiagnostics(),
        bug_report=None,
    )


def test_returns_referenced_screenshot(
    tmp_path,
):
    runs_directory = tmp_path / "runs"
    run_directory = runs_directory / "run123"

    run_directory.mkdir(
        parents=True
    )

    screenshot_path = (
        run_directory / "step_1.png"
    )

    screenshot_path.write_bytes(
        b"fake image data"
    )

    run = create_stored_run(
        str(screenshot_path)
    )

    service = ArtifactService(
        runs_directory=str(runs_directory)
    )

    result = service.get_screenshot(
        run=run,
        filename="step_1.png",
    )

    assert result == screenshot_path.resolve()


def test_rejects_path_traversal(
    tmp_path,
):
    service = ArtifactService(
        runs_directory=str(tmp_path)
    )

    run = create_stored_run(
        str(tmp_path / "step_1.png")
    )

    with pytest.raises(
        InvalidArtifactNameError
    ):
        service.get_screenshot(
            run=run,
            filename="../step_1.png",
        )


def test_rejects_unreferenced_screenshot(
    tmp_path,
):
    runs_directory = tmp_path / "runs"
    run_directory = runs_directory / "run123"

    run_directory.mkdir(
        parents=True
    )

    referenced_path = (
        run_directory / "step_1.png"
    )

    referenced_path.write_bytes(
        b"referenced image"
    )

    unreferenced_path = (
        run_directory / "secret.png"
    )

    unreferenced_path.write_bytes(
        b"unreferenced image"
    )

    run = create_stored_run(
        str(referenced_path)
    )

    service = ArtifactService(
        runs_directory=str(runs_directory)
    )

    with pytest.raises(
        ArtifactNotFoundError
    ):
        service.get_screenshot(
            run=run,
            filename="secret.png",
        )
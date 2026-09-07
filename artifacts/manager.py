from pathlib import Path
import os
import re
import shutil
import stat


BASE_ARTIFACT_DIR = Path(
    os.getenv(
        "ARTIFACTS_DIR",
        "artifacts/generated"
    )
).resolve()


MAX_ARTIFACT_SIZE = 5 * 1024 * 1024


SAFE_FILENAME_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,119}$"
)


def _validate_task_id(
    task_id: int
) -> int:

    if (
        not isinstance(task_id, int)
        or isinstance(task_id, bool)
        or task_id <= 0
    ):

        raise ValueError(
            "Task ID must be a positive integer."
        )

    return task_id


def sanitize_filename(
    filename: str
) -> str:

    if not isinstance(
        filename,
        str
    ):

        raise TypeError(
            "Filename must be a string."
        )

    filename = filename.strip()

    if not filename:

        raise ValueError(
            "Filename cannot be empty."
        )

    if (
        "/" in filename
        or "\\" in filename
    ):

        raise ValueError(
            "Path separators are not allowed "
            "in artifact filenames."
        )

    if filename in {
        ".",
        ".."
    }:

        raise ValueError(
            "Invalid artifact filename."
        )

    if not SAFE_FILENAME_PATTERN.fullmatch(
        filename
    ):

        raise ValueError(
            "Artifact filename contains "
            "unsupported characters."
        )

    return filename


def _get_task_directory(
    task_id: int
) -> Path:

    task_id = _validate_task_id(
        task_id
    )

    task_directory = (
        BASE_ARTIFACT_DIR /
        str(task_id)
    ).resolve()

    if (
        BASE_ARTIFACT_DIR !=
        task_directory
        and BASE_ARTIFACT_DIR not in
        task_directory.parents
    ):

        raise RuntimeError(
            "Invalid artifact directory."
        )

    task_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    return task_directory


def get_artifact_path(
    task_id: int,
    filename: str
) -> Path:

    task_directory = _get_task_directory(
        task_id
    )

    safe_filename = sanitize_filename(
        filename
    )

    artifact_path = (
        task_directory /
        safe_filename
    ).resolve()

    if (
        BASE_ARTIFACT_DIR not in
        artifact_path.parents
    ):

        raise RuntimeError(
            "Invalid artifact path."
        )

    return artifact_path


def save_artifact(
    task_id: int,
    filename: str,
    content: str | bytes
) -> dict:

    artifact_path = get_artifact_path(
        task_id,
        filename
    )

    if isinstance(
        content,
        str
    ):

        data = content.encode(
            "utf-8"
        )

    elif isinstance(
        content,
        (bytes, bytearray)
    ):

        data = bytes(content)

    else:

        raise TypeError(
            "Artifact content must be "
            "a string or bytes."
        )

    if len(data) > MAX_ARTIFACT_SIZE:

        raise ValueError(
            "Artifact exceeds the maximum "
            "allowed size of 5 MB."
        )

    artifact_path.write_bytes(
        data
    )

    return {
        "filename":
            artifact_path.name,

        "size_bytes":
            len(data),

        "path":
            str(
                artifact_path.relative_to(
                    BASE_ARTIFACT_DIR
                )
            )
    }


def list_artifacts(
    task_id: int
) -> list[dict]:

    task_directory = _get_task_directory(
        task_id
    )

    artifacts = []

    for artifact_path in sorted(
        task_directory.iterdir(),
        key=lambda path: path.name.lower()
    ):

        if not artifact_path.is_file():

            continue

        resolved_path = (
            artifact_path.resolve()
        )

        if (
            BASE_ARTIFACT_DIR not in
            resolved_path.parents
        ):

            continue

        artifacts.append(
            {
                "filename":
                    artifact_path.name,

                "size_bytes":
                    artifact_path.stat().st_size,

                "path":
                    str(
                        artifact_path.relative_to(
                            BASE_ARTIFACT_DIR
                        )
                    )
            }
        )

    return artifacts


def _remove_readonly(
    func,
    path,
    exc_info
):
    """
    Retry filesystem deletion after removing
    the read-only attribute.

    This is useful on Windows/OneDrive where
    generated files can occasionally be marked
    read-only.
    """

    try:

        os.chmod(
            path,
            stat.S_IWRITE
        )

        func(
            path
        )

    except OSError:

        raise


def delete_task_artifacts(
    task_id: int
) -> bool:

    task_id = _validate_task_id(
        task_id
    )

    task_directory = (
        BASE_ARTIFACT_DIR /
        str(task_id)
    ).resolve()

    if (
        BASE_ARTIFACT_DIR not in
        task_directory.parents
    ):

        raise RuntimeError(
            "Invalid artifact directory."
        )

    if not task_directory.exists():

        return False

    if not task_directory.is_dir():

        raise RuntimeError(
            "Artifact path is not a directory."
        )

    shutil.rmtree(
        task_directory,
        onerror=_remove_readonly
    )

    return True
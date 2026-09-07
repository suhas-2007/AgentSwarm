from pathlib import Path
import shutil

from artifacts.manager import (
    BASE_ARTIFACT_DIR,
    save_artifact,
    list_artifacts,
    get_artifact_path,
    delete_task_artifacts,
)


TEST_TASK_ID = 999999


def main():
    print("=" * 60)
    print("AgentSwarm Local Artifact Test")
    print("=" * 60)

    # ---------------------------------------------------------
    # CLEAN OLD TEST DATA
    # ---------------------------------------------------------

    test_dir = BASE_ARTIFACT_DIR / str(TEST_TASK_ID)

    if test_dir.exists():
        shutil.rmtree(test_dir)

    print("\n[1] Saving test artifact...")

    result = save_artifact(
        TEST_TASK_ID,
        "local_test_code.txt",
        "print('AgentSwarm artifact test successful')\n"
    )

    print("Saved:")
    print(result)

    # ---------------------------------------------------------
    # LIST ARTIFACTS
    # ---------------------------------------------------------

    print("\n[2] Listing artifacts...")

    artifacts = list_artifacts(TEST_TASK_ID)

    print(artifacts)

    assert len(artifacts) == 1
    assert artifacts[0]["filename"] == "local_test_code.txt"

    # ---------------------------------------------------------
    # CHECK PATH
    # ---------------------------------------------------------

    print("\n[3] Checking artifact path...")

    artifact_path = get_artifact_path(
        TEST_TASK_ID,
        "local_test_code.txt"
    )

    print("Path:")
    print(artifact_path)

    assert artifact_path.is_file()

    # ---------------------------------------------------------
    # CHECK CONTENT
    # ---------------------------------------------------------

    print("\n[4] Checking artifact content...")

    content = artifact_path.read_text(
        encoding="utf-8"
    )

    print(content)

    assert "AgentSwarm artifact test successful" in content

    # ---------------------------------------------------------
    # PATH TRAVERSAL TEST
    # ---------------------------------------------------------

    print("\n[5] Testing filename security...")

    try:
        get_artifact_path(
            TEST_TASK_ID,
            "../dangerous.txt"
        )

        raise AssertionError(
            "Path traversal was not blocked."
        )

    except ValueError:
        print("Path traversal blocked correctly.")

    # ---------------------------------------------------------
    # DELETE TEST
    # ---------------------------------------------------------

    print("\n[6] Testing artifact deletion...")

    deleted = delete_task_artifacts(
        TEST_TASK_ID
    )

    print("Deleted:", deleted)

    assert deleted is True
    assert not test_dir.exists()

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("ALL ARTIFACT TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
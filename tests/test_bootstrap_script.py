import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "bootstrap-deployment.sh"


def test_bootstrap_script_help() -> None:
    subprocess.run(["bash", "-n", SCRIPT], check=True)
    result = subprocess.run([SCRIPT, "--help"], check=True, capture_output=True, text=True)

    assert "AWS_PROFILE" in result.stdout
    assert "GITHUB_REPOSITORY" in result.stdout
    assert "never creates access keys" in result.stdout


def test_bootstrap_existing_resources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    aws = bin_dir / "aws"
    aws.write_text(
        """#!/bin/sh
case "$*" in
  *"sts get-caller-identity"*) echo 123456789012 ;;
  *"iam get-open-id-connect-provider"*"contains(ClientIDList"*) echo True ;;
  *"iam get-role"*"Role.Arn"*) echo arn:aws:iam::123456789012:role/test ;;
esac
exit 0
"""
    )
    aws.chmod(0o755)

    gh = bin_dir / "gh"
    gh.write_text("#!/bin/sh\nexit 0\n")
    gh.chmod(0o755)

    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    monkeypatch.setenv("AWS_PROFILE", "test-profile")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repository")
    monkeypatch.setenv("BOOTSTRAP_APPROVED", "true")

    result = subprocess.run([SCRIPT], check=True, capture_output=True, text=True)

    assert "Bootstrap complete" in result.stdout

"""Validate the docker-compose configuration.

The compose file must parse cleanly after adding the postgres and nginx
services. If the standalone ``docker-compose`` binary is not installed the
test is skipped (the ``docker compose`` plugin is used for local checks
instead).
"""

import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("docker-compose") is None,
    reason="docker-compose not available",
)


def test_compose_config_valid():
    result = subprocess.run(
        ["docker-compose", "config", "--quiet"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

"""Validate the docker-compose configuration.

The compose file must parse cleanly after adding the postgres and nginx
services. If the standalone ``docker-compose`` binary is not installed the
``test_compose_config_valid`` test is skipped (the ``docker compose`` plugin
is used for local checks instead).

The postgres service must mount the ``postgres_data`` volume so database
data survives ``docker-compose down && up``.
"""

import shutil
import subprocess

import pytest


@pytest.mark.skipif(
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


def test_postgres_volume_defined():
    import yaml

    with open("docker-compose.yml") as f:
        cfg = yaml.safe_load(f)
    volumes = cfg["services"]["postgres"]["volumes"]
    assert any("postgres_data" in v for v in volumes)

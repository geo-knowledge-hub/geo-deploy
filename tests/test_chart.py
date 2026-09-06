#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test chart rendering."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from gkh_deploy import profiles, render
from gkh_deploy.render import k8s

#
# Constants - Environment variables
#
CHART = os.environ.get("GKH_CHART_PATH", "")


#
# Markers
#
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm"),
    pytest.mark.skipif(not CHART or not Path(CHART).is_dir(), reason="needs GKH_CHART_PATH"),
]


#
# Auxiliary functions
#
def helm_template(values_path):
    return subprocess.run(
        ["helm", "template", "invenio", CHART, "-f", str(values_path)],
        capture_output=True,
        text=True,
    )


def documents(result):
    """Get the documents from the result."""
    return [d for d in yaml.safe_load_all(result.stdout) if d]


def secret_key_refs(node):
    """Every (secret, key) pair the manifests read, wherever it appears."""
    if isinstance(node, dict):
        reference = node.get("secretKeyRef")

        if isinstance(reference, dict):
            yield reference["name"], reference["key"]

        for value in node.values():
            yield from secret_key_refs(value)

    elif isinstance(node, list):
        for value in node:
            yield from secret_key_refs(value)


def secrets_in_manifests(result):
    """The (secret, key) pairs the chart creates itself."""
    return {
        (d["metadata"]["name"], key)
        for d in documents(result)
        if d.get("kind") == "Secret"
        for key in d.get("data") or {}
    }


def secrets_in_script(script):
    """The (secret, key) pairs secrets.sh creates."""
    blocks = re.split(r"^create_secret ", script, flags=re.M)[1:]

    return {
        (block.split()[0].strip('"'), key)
        for block in blocks
        for key in re.findall(r"--from-literal=([^=]+)=", block)
    }


def invenio_config(result):
    """The application ConfigMap the chart builds from hostname plus extraConfig."""
    maps = [
        d
        for d in documents(result)
        if d.get("kind") == "ConfigMap" and "INVENIO_SITE_UI_URL" in (d.get("data") or {})
    ]

    # assert
    assert len(maps) == 1

    # return the data
    return maps[0]["data"]


#
# Fixtures
#
@pytest.fixture(params=["minimal", "standard"])
def rendered(request, tmp_path):
    """A generated bundle, passed through helm template."""
    # load the profile
    answers = profiles.load(request.param)
    answers["hostname"] = "gkhub.example.org"
    answers["admin"]["email"] = "admin@example.org"
    answers["datacite"]["prefix"] = "10.5072"

    # write the bundle
    render.write(render.bundle(answers), tmp_path)
    result = helm_template(tmp_path / "values.yaml")

    # assert
    assert result.returncode == 0, result.stderr

    return result


def test_the_chart_accepts_the_generated_values(rendered):
    assert len(documents(rendered)) > 20


def test_helm_reports_no_warnings(rendered):
    assert "warning" not in rendered.stderr.lower(), rendered.stderr


def test_every_secret_reference_resolves(rendered, tmp_path):
    """A secretKeyRef whose Secret, or whose key within it, is never created."""
    provided = secrets_in_manifests(rendered) | secrets_in_script(
        (tmp_path / "secrets.sh").read_text()
    )

    assert set(secret_key_refs(documents(rendered))) - provided == set()


def test_no_credential_is_a_literal_in_a_pod_environment(rendered):
    for variable in ("INVENIO_DB_PASSWORD", "INVENIO_AMQP_BROKER_PASSWORD"):
        assert not re.search(rf"name: {variable}\n\s*value:", rendered.stdout), variable


def test_the_hostname_reaches_every_place_that_needs_it(rendered):
    config = invenio_config(rendered)

    # url
    assert config["INVENIO_SITE_UI_URL"] == "https://gkhub.example.org"
    assert config["INVENIO_SITE_API_URL"] == "https://gkhub.example.org/api"

    # allowed hosts
    assert "gkhub.example.org" in config["INVENIO_APP_ALLOWED_HOSTS"]
    assert "gkhub.example.org" in config["INVENIO_TRUSTED_HOSTS"]


def test_both_ratelimit_storage_spellings_reach_the_same_redis(rendered):
    # The chart sets only the URI, which flask-limiter 1.1.0 does not read. The bundle
    # adds the _URL spelling, and the chart resolves the host expression inside it.
    config = invenio_config(rendered)

    assert config["INVENIO_RATELIMIT_STORAGE_URI"].startswith("redis://")
    assert config["INVENIO_RATELIMIT_STORAGE_URL"] == config["INVENIO_RATELIMIT_STORAGE_URI"]


def test_the_worker_is_discoverable_by_the_selector_bootstrap_uses(rendered):
    workers = [
        d
        for d in documents(rendered)
        if d.get("kind") == "Deployment"
        and (d["metadata"].get("labels") or {}).get("app.kubernetes.io/component") == "worker"
        and (d["metadata"].get("labels") or {}).get("app.kubernetes.io/name") == "invenio"
    ]

    # assert
    assert len(workers) == 1

    # get the containers
    containers = workers[0]["spec"]["template"]["spec"]["containers"]

    # assert
    assert any(c["name"] == k8s.WORKER_CONTAINER for c in containers)


def test_no_install_init_job_is_created(rendered):
    # bootstrap owns the sequence, so the chart's job must stay off
    assert not [d for d in documents(rendered) if d.get("kind") == "Job"]


def test_an_unknown_key_really_does_vanish(tmp_path):
    answers = profiles.load("minimal")
    answers["hostname"] = "gkhub.example.org"
    answers["admin"]["email"] = "admin@example.org"
    answers["extra_values"] = {"app": {"extraConfig": {"INVENIO_INERT": "yes"}}}

    # write the bundle
    render.write(render.bundle(answers), tmp_path)
    result = helm_template(tmp_path / "values.yaml")

    # assert
    assert result.returncode == 0
    assert "INVENIO_INERT" not in result.stdout


def test_the_datacite_footgun_renders_a_dangling_reference(tmp_path):
    values = {
        "invenio": {
            "hostname": "gkhub.example.org",
            "datacite": {
                "enabled": True,
                "username": "u",
                "password": "p",
                "existingSecret": "datacite-secrets",
                "prefix": "10.5072",
                "testMode": "True",
            },
        },
        "postgresql": {
            "auth": {"existingSecret": "s", "secretKeys": {"userPasswordKey": "password"}}
        },
        "rabbitmq": {"auth": {"existingPasswordSecret": "s", "existingSecretPasswordKey": "k"}},
    }

    # write the values
    path = tmp_path / "values.yaml"
    path.write_text(yaml.safe_dump(values))

    # template the values
    result = helm_template(path)

    # assert
    assert result.returncode == 0

    # assert the secret is in the output
    assert "datacite-secrets" in result.stdout
    assert not [
        d
        for d in yaml.safe_load_all(result.stdout)
        if d and d.get("kind") == "Secret" and d["metadata"]["name"] == "datacite-secrets"
    ]

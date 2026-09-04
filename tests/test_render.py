#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test rendering."""

import yaml

from gkh_deploy import CHART_VERSION, profiles, render, rules

#
# Constants - Bundle files
#
BUNDLE = [
    "README.md",
    "bootstrap.sh",
    "gkh-deploy.yaml",
    "secrets.sh",
    "values.yaml",
]


def test_the_bundle_holds_the_five_expected_files_each_ending_in_a_newline(settings):
    # render the bundle
    files = render.bundle(settings)

    # assert
    assert sorted(files) == BUNDLE
    assert all(body.endswith("\n") for body in files.values())
    assert CHART_VERSION in files["README.md"]


def test_rendering_is_deterministic(settings):
    assert render.bundle(settings) == render.bundle(settings)


def test_both_shipped_profiles_render_values_that_pass_every_check():
    for name in profiles.names():
        answers = profiles.load(name)

        answers["hostname"] = "gkhub.example.org"
        answers["admin"]["email"] = "admin@example.org"
        answers["datacite"]["prefix"] = "10.5072"

        assert rules.check(render.values(answers)) == [], name


def test_no_credential_is_a_literal_and_the_database_password_comes_from_a_secret(settings):
    # get bundle body
    body = "\n".join(render.bundle(settings).values())

    # get the auth
    auth = render.values(settings)["postgresql"]["auth"]

    # assert
    assert "dbpassword" not in body
    assert "mqpassword" not in body
    assert auth["existingSecret"] == settings["secrets"]["postgresql"]
    assert "password" not in auth


def test_the_hostname_and_the_users_extras_reach_the_values(settings):
    # set the extra config
    settings["extra_config"] = {"INVENIO_CUSTOM": "value"}

    # set the extra values
    settings["extra_values"] = {"nodeSelector": {"disk": "ssd"}}
    values = render.values(settings)

    # test subscriptions
    assert settings["hostname"] in values["invenio"]["extraConfig"]["INVENIO_APP_ALLOWED_HOSTS"]
    assert values["invenio"]["extraConfig"]["INVENIO_CUSTOM"] == "value"
    assert values["nodeSelector"] == {"disk": "ssd"}


def test_datacite_renders_a_secret_reference_when_enabled_and_nothing_when_not(settings):
    # test datacite activation
    assert render.values(settings)["invenio"]["datacite"] == {"enabled": False}

    # set datacite activation
    settings["datacite"]["enabled"] = True
    settings["datacite"]["prefix"] = "10.5072"
    datacite = render.values(settings)["invenio"]["datacite"]

    # assert
    assert datacite["username"] == ""
    assert datacite["existingSecret"] == settings["datacite"]["secret_name"]


def test_the_bundle_records_the_settings_it_came_from_and_writes_the_scripts_executable(
    settings, tmp_path
):
    # write the bundle
    render.write(render.bundle(settings), tmp_path)

    # assert
    assert yaml.safe_load((tmp_path / "gkh-deploy.yaml").read_text()) == settings
    assert (tmp_path / "secrets.sh").stat().st_mode & 0o111
    assert (tmp_path / "bootstrap.sh").stat().st_mode & 0o111

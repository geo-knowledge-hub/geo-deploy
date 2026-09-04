#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test settings."""

import yaml

from gkh_deploy import settings as settings_module


def test_what_dump_writes_is_what_load_reads_back(settings, tmp_path):
    path = tmp_path / "gkh-deploy.yaml"
    path.write_text(settings_module.dump(settings))

    assert settings_module.load(path) == settings
    assert yaml.safe_load(path.read_text()) == settings

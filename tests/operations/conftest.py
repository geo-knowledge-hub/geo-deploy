#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Configuration for operations tests."""

import pytest
import yaml


@pytest.fixture
def config_file(tmp_path):
    """Configuration file fixture."""

    def write(settings):
        path = tmp_path / "gkh-deploy.yaml"
        path.write_text(yaml.safe_dump(settings))

        return path

    return write

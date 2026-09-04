#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test profiles."""

import pytest

from gkh_deploy import profiles
from gkh_deploy import settings as settings_module


def test_shipped_profiles_are_listed():
    assert profiles.names() == ["minimal", "standard"]


def test_every_shipped_profile_validates_once_the_answers_are_filled_in():
    for name in profiles.names():
        answers = profiles.load(name)

        answers["hostname"] = "gkhub.example.org"
        answers["admin"]["email"] = "admin@example.org"
        answers["datacite"]["prefix"] = "10.5072"

        assert settings_module.validate(answers) == [], name


def test_an_unknown_profile_says_what_is_available():
    with pytest.raises(FileNotFoundError, match="minimal, standard"):
        profiles.load("nope")

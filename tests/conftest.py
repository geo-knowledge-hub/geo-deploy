import pytest

from gkh_deploy import profiles


@pytest.fixture
def settings():
    """A valid minimal configuration."""

    answers = profiles.load("minimal")
    answers["hostname"] = "gkhub.example.org"
    answers["admin"]["email"] = "admin@example.org"

    return answers

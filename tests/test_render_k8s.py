#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test rendering Kubernetes resources."""

from gkh_deploy.render import k8s


def test_the_selector_scopes_to_the_chart_and_the_worker():
    selector = k8s.worker_selector()

    assert "app.kubernetes.io/name=invenio" in selector
    assert "app.kubernetes.io/component=worker" in selector


def test_a_release_scopes_the_selector_further_and_no_release_leaves_it_out():
    assert "app.kubernetes.io/instance=prod" in k8s.worker_selector("prod")
    assert "instance" not in k8s.worker_selector()

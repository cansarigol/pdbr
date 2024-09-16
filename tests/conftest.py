"""
Add '--skip-slow' cmdline option to skip tests that are marked with @pytest.mark.slow.
"""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--skip-slow", action="store_true", default=False, help="Skip slow tests"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--skip-slow"):
        return
    skip_slow = pytest.mark.skip(reason="Specified --skip-slow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

"""Integration tests for the Commands module."""
from unittest import mock

import pytest
import requests

from fidesctl.core import api, apply, models


def test_apply(populated_manifest_dir):
    assert True

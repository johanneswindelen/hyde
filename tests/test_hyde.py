import unittest
from unittest import mock

import tempfile
from pathlib import Path
from anytree import Node

from hyde.hyde import Hyde


class TestHyde(unittest.TestCase):
    def test_build_site_tree(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Hyde.new_site(tmpdir + "/test")

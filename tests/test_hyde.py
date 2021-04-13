import unittest
from unittest import mock

from pathlib import Path
from bs4 import BeautifulSoup

from hyde import Hyde
from .utils import *


class TestHyde(unittest.TestCase):
    def setUp(self):
        self.pages = [page_from_file_str(p) for p in TEST_NAV_BAR_FILES + TEST_PAGE_FILES]

    def test_hyde_sort_content_pages(self):
        non_paged, paged = Hyde()._sort_content_pages(self.pages)

        self.assertEqual(len(non_paged), 1)
        self.assertIn("posts", paged.keys())
        self.assertEqual(len(paged["posts"]), 3)
        self.assertEqual(non_paged[0].meta.title, "Homepage")
        titles = [p.meta.title for p in paged["posts"]]
        self.assertIn("Test post", titles)
        self.assertIn("Test post 2", titles)
        self.assertIn("Test post 3", titles)

    def test_hyde_render_content_html(self):
        non_paged, paged = Hyde()._sort_content_pages(self.pages)

        h = Hyde()
        h.jinja2_env = get_jinja2_env()

        rendered_html = h._render_content_to_html(non_paged, paged)
        print(rendered_html) # FIXME
        soup = BeautifulSoup(rendered_html, features="html.parser")

        assert_expected_hrefs_in_soup(soup, ["/posts/index.html"])
        
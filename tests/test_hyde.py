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
        singles, paginators = Hyde()._sort_content(self.pages)

        self.assertEqual(len(singles), 2)
        self.assertEqual(paginators[0].path, "posts")
        self.assertEqual(paginators[0].number_pages, 1)
        self.assertEqual(paginators[1].path, "_private")
        self.assertEqual(paginators[1].number_pages, 1)
        self.assertEqual(singles[0].meta.title, "Homepage")
        self.assertEqual(singles[1].meta.title, "About me")

    def test_hyde_render_content_html_contains_navlinks(self):
        singles, paginators = Hyde()._sort_content(self.pages)

        h = Hyde()
        h.jinja2_env = get_jinja2_env()

        # take any website, it should contain the navbar links
        _, rendered_html = h._render_content_to_html(singles, paginators)[0]
        soup = BeautifulSoup(rendered_html, features="html.parser")

        assert_expected_hrefs_in_soup(soup, ["/posts/index.html", "/index.html", "/about.html"])
        
    # def test_hyde_private_content_available_through_magic_link(self):
    #     raise

    # def test_hyde_private_content_not_available_without_magic_link(self):
    #     raise
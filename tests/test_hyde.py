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

        self.assertEqual(len(non_paged), 2)
        self.assertIn("posts", paged.keys())
        self.assertEqual(len(paged["posts"]), 3)
        self.assertEqual(non_paged[0].meta.title, "Homepage")
        self.assertEqual(non_paged[1].meta.title, "About me")
        titles = [p.meta.title for p in paged["posts"]]
        self.assertIn("Test post", titles)
        self.assertIn("Test post 2", titles)
        self.assertIn("Test post 3", titles)

    def test_hyde_render_content_html_contains_navlinks(self):
        non_paged, paged = Hyde()._sort_content_pages(self.pages)

        h = Hyde()
        h.jinja2_env = get_jinja2_env()

        nav_bar = h._render_navbar_html(non_paged, paged)

        # take any website, it should contain the navbar links
        _, rendered_html = h._render_content_to_html(non_paged, paged, nav_bar)[0]
        soup = BeautifulSoup(rendered_html, features="html.parser")

        assert_expected_hrefs_in_soup(soup, ["/posts/index.html", "/index.html", "/about.html"])
        
    # def test_hyde_magic_generate_folders_for_private_content(self):
    #     raise

    # def test_hyde_private_content_available_through_magic_link(self):
    #     raise

    # def test_hyde_private_content_not_available_without_magic_link(self):
    #     raise
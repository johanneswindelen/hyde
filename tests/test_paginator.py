from unittest import mock
import unittest
from bs4 import BeautifulSoup

from hyde.pages import Page
from hyde.paginator import Paginator
from .utils import *

class PaginatorTests(unittest.TestCase):
    def setUp(self):
        self.pages = [page_from_file_str(test_file) for test_file in TEST_PAGE_FILES]
    
    def tearDown(self):
        del self.pages
        
    def test_paginator_with_pages(self):      
        paginator = Paginator(name="posts", content=self.pages, items_per_page=2)
        self.assertEqual(paginator.number_pages, 2)

        index = next(paginator)
        self.assertEqual(len(index.items), 2)
        self.assertEqual(index.items[0].meta.title, "Test post")
        self.assertEqual(index.items[0].url, "/posts/test-title-stub.html")
        self.assertEqual(index.number, 0)
        self.assertEqual(index.url, "/posts/index.html")
        index = next(paginator)
        self.assertEqual(len(index.items), 1)
        self.assertEqual(index.items[0].meta.title, "Test post 3")
        self.assertEqual(index.items[0].url, "/posts/test-post-3.html")
        self.assertEqual(index.number, 1)
        self.assertEqual(index.url, "/posts/index2.html")

    def test_paginator_length_items_smaller_items_per_page(self):
        paginator = Paginator(name="posts", content=self.pages, items_per_page=10)
        self.assertEqual(paginator.number_pages, 1)

        index = next(paginator)
        self.assertEqual(len(index.items), 3)

    def test_paginator_prev_next_links(self):
        paginator = Paginator(name="posts", content=self.pages, items_per_page=1)

        index = next(paginator)
        self.assertEqual(paginator.has_next, True)
        self.assertEqual(paginator.has_prev, False)
        index = next(paginator)
        self.assertEqual(paginator.has_next, True)
        self.assertEqual(paginator.has_prev, True)
        index = next(paginator)
        self.assertEqual(paginator.has_next, False)
        self.assertEqual(paginator.has_prev, True)

    def souped_index(self, paginator):
        index = next(paginator)
        html_doc = index.render(get_jinja2_env(), paginator, nav_bar_pages=nav_bar_pages)
        return BeautifulSoup(html_doc, features="html.parser")

    def test_paginator_render_contains_links(self):
        paginator = Paginator(name="posts", content=self.pages, items_per_page=10)
        soup = self.souped_index(paginator)

        assert_expected_hrefs_in_soup(soup, ["/posts/test-title-stub.html", "/posts/test-post-2.html", "/posts/test-post-3.html"])
        assert_expected_a_texts_in_soup(soup, ["Test post", "Test post 2", "Test post 3"])

    def test_paginator_render_has_prev_next_links(self):
        paginator = Paginator(name="posts", content=self.pages, items_per_page=1)
        soup = self.souped_index(paginator)
        assert_expected_hrefs_in_soup(soup, ["/posts/index2.html"])

        soup = self.souped_index(paginator)
        assert_expected_hrefs_in_soup(soup, ["/posts/index.html", "/posts/index3.html"])

        soup = self.souped_index(paginator)
        assert_expected_hrefs_in_soup(soup, ["/posts/index2.html"])

    def test_paginator_render_has_nav_bar(self):
        paginator = Paginator(name="posts", content=self.pages, items_per_page=1)
        soup = self.souped_index(paginator)

        assert_expected_hrefs_in_soup(soup, ["/index.html"])

    def test_paginator_should_not_have_side_effects_on_content(self):
        paginator = Paginator(name="posts", content=self.pages, items_per_page=10)
        paginator = Paginator(name="posts", content=self.pages, items_per_page=10)
        soup = self.souped_index(paginator)

        assert_expected_hrefs_in_soup(soup, ["/posts/test-title-stub.html", "/posts/test-post-2.html", "/posts/test-post-3.html"])
        assert_expected_a_texts_in_soup(soup, ["Test post", "Test post 2", "Test post 3"])
from pathlib import Path
import jinja2

from unittest import mock
from hyde.pages import ContentPage

def get_jinja2_env():
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader("src/hyde/scaffolding/templates"),
    ) 

def page_from_file_str(test_file: str):
    with mock.patch('hyde.pages.open', mock.mock_open(read_data=test_file["content"])) as m:
        return ContentPage.from_file(test_file["file_path"], Path("content"))

def assert_expected_hrefs_in_soup(soup, expected):
    links = [a.get("href") for a in soup.find_all('a')]
    for expected_href in expected:
        assert expected_href in links

def assert_expected_a_texts_in_soup(soup, expected):
    titles = [a.string for a in soup.find_all('a')]
    for expected_title in expected:
        assert expected_title in titles

TEST_NAV_BAR_FILES = [
    {
        "file_path": Path("content/index.md"),
        "content": """
author: Hyde
draft: False
date: 2021-03-01
template: home
title: Homepage
urlstub: index
---
# Welcome to hyde
        """
    },
    {
        "file_path": Path("content/about.md"),
        "content": """
author: Hyde
draft: False
date: 2021-03-01
template: home
title: About me
urlstub: about
---
# Welcome to the about me page!
        """
    }
]

def get_navbar():
    nav_template = get_jinja2_env().get_template("navbar.html.jinja2")
    return nav_template.render(nav_bar_pages=[page_from_file_str(p) for p in TEST_NAV_BAR_FILES])

# only one level of content grouping is allowed using the path!
INVALID_PATH_FILE =  {
    "file_path": Path("content/invalid/posts/test_title.md"),
    "content": """
title: Invalid Path
urlstub: invalid-path
---
Testing
"""
}

TEST_PAGE_FILES = [
    {
    "file_path": Path("content/posts/test_title.md"),
    "content": """
author: Hyde
draft: False
date: 2021-03-01
template: post
title: Test post
urlstub: test-title-stub
---
# Welcome to hyde

How are you today?
""",
    "html": "<h1>Welcome to hyde</h1>\n<p>How are you today?</p>"
},
{
    "file_path": Path("content/posts/test_title_2.md"),
    "content": """
author: Hyde
draft: False
date: 2021-03-02
title: Test post 2
urlstub: test-post-2
---
# Welcome to hyde, again

How are you today?
""",
    "html": "<h1>Welcome to hyde, again</h1>\n<p>How are you today?</p>",
},
{
    "file_path": Path("content/posts/test_title_3.md"),
    "content": """
author: Hyde
draft: False
date: 2021-03-02
title: Test post 3
urlstub: test-post-3
---
# Welcome to hyde, and one more time!

How are you today?
""",
    "html": "<h1>Welcome to hyde, and one more time!</h1>\n<p>How are you today?</p>",
}]

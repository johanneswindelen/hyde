from pathlib import Path
import jinja2

from unittest import mock
from hyde.pages import Page

def get_jinja2_env():
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader("src/hyde/scaffolding/templates"),
    ) 

def page_from_file_str(test_file: str):
    with mock.patch('hyde.pages.open', mock.mock_open(read_data=test_file["content"])) as m:
        return Page.from_file(test_file["file_path"])

TEST_PAGE_FILES = [
    {
    "file_path": Path("content/posts/test_title.md"),
    "content": """
author: Hyde
draft: False
date: 2021-03-01
type: posts
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
type: posts
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
type: posts
title: Test post 3
urlstub: test-post-3
---
# Welcome to hyde, and one more time!

How are you today?
""",
    "html": "<h1>Welcome to hyde, and one more time!</h1>\n<p>How are you today?</p>",
}]

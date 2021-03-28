import math
from itertools import tee, islice, chain

from hyde.pages import Page

class Index(object):
    def __init__(self, name: str, pages: list[Page], number: int):
        self._name = name
        self._items = pages
        self._number = number

    @property
    def items(self):
        return self._items

    @property
    def name(self):
        return self._name

    @property
    def number(self):
        return self._number

    @property
    def url(self):
        return f"{self._name}/index{self._number + 1 if self._number > 0 else ''}.html"

    @property
    def html_path(self):
        return Path(self.url)

    def render(self, jinja2_env, paginator):
        template_name = f"index.html.jinja2"
        template = jinja2_env.get_template(template_name)
        rendered_html = template.render(index=self, children=self._items, paginator=paginator)
        return rendered_html


class Paginator(object):
    def __init__(self, name: str, content: list[Page], items_per_page: int = 10):
        self._content = content
        self._items_per_page = items_per_page
        self._name = name

        self._number_pages = math.ceil(len(content) / self._items_per_page)
        self._prev = self._current = self._next = None
        self._indices = self._build_indices()
        self._indices_iters = self._buid_indices_iter()

    @property
    def number_pages(self):
        return self._number_pages

    @property
    def name(self):
        return self._name

    @property
    def has_next(self):
        return self._next is not None
    
    @property
    def has_prev(self):
        return self._prev is not None

    @property
    def prev(self):
        return self._prev

    @property
    def next(self):
        return self._next

    @property
    def url(self):
        return f"{self._name}/"

    def _build_indices(self):
        indices = []
        for index_number in range(self._number_pages):
            start_index = index_number * self._items_per_page
            end_index = (index_number + 1) * self._items_per_page

            try:
                index = Index(self._name, self._content[start_index:end_index], index_number)
            except IndexError:
                index = Index(self._name, self._content[start_index:], index_number)
            indices.append(index)
        return indices

    def _buid_indices_iter(self):
        prevs, curs, nexts = tee(self._indices, 3)
        prevs = chain([None], prevs)
        nexts = chain(islice(nexts, 1, None), [None])
        return zip(prevs, curs, nexts)

    def __next__(self):
        # will raise StopIteration when _iter_indices is exhausted
        self._prev, current, self._next = next(self._indices_iters)
        return current

    def __iter__(self):
        return self
        
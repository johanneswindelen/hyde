import math
from itertools import tee, islice, chain

from hyde import IndexPage, ContentPage


class Paginator(object):
    def __init__(self, name: str, content: list[ContentPage], items_per_page: int = 10):
        self._content = content
        self._items_per_page = items_per_page
        self._name = name

        self._number_pages = math.ceil(len(content) / self._items_per_page)
        self._prev = self._current = self._next = None
        self._indices = self._build_indices()
        self._indices_iters = self._buid_indices_iter()

        # rewrite URLs of member content pages
        for p in self._content:
            p.url = f"/{name}{p.url}"

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
        return f"/{self._name}/"

    def _build_indices(self):
        indices = []
        for index_number in range(self._number_pages):
            start_index = index_number * self._items_per_page
            end_index = (index_number + 1) * self._items_per_page

            try:
                index = IndexPage(self._name, self._content[start_index:end_index], index_number)
            except IndexError:
                index = IndexPage(self._name, self._content[start_index:], index_number)
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
        
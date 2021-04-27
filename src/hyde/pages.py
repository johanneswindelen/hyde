from dataclasses import dataclass
from datetime import date
from markdown import markdown
from pathlib import Path
import yaml
import sys
import logging

METADATA_SEP = "---"

logger = logging.getLogger("hyde")


@dataclass
class Metadata(object):
    title: str
    urlstub: str
    content_group: str = None
    template: str = "post"
    draft: bool = False
    date: date = None
    author: str = None


class Page(object):
    def __init__(self, meta: Metadata, url: str):
        self.meta = meta
        self._url = url

    @property
    def template_file(self):
        return f"{self.meta.template}.html.jinja2"

    @property
    def html_path(self):
        return Path(self._url.lstrip("/"))

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, v):
        if not v.startswith("/"):
            raise HydeError(f"URLs must be absolute, got '{v}'")
        self._url = v

    def render(self, *args):
        raise NotImplementedError("render_html should be implemented in child classes!")


class ContentPage(Page):
    def __init__(self, meta: Metadata, content: str):
        url = f"/{meta.urlstub}.html"
        if meta.content_group:
            url = f"/{meta.content_group}{url}"

        super().__init__(meta, url)
        self.content = content

    @classmethod
    def from_file(cls, path: Path):
        with open(path, "r") as f:
            text = f.read()

        parent = Path("/".join(path.parts[1:])).parent
        if len(parent.parts) > 1:
            logger.error(f"Hyde doesn't support nested content!")
            logger.error(f"Couldn't parse content file '{path}'")
            sys.exit(1)
        content_group = None if parent == Path('.') else parent.name
        
        try:
            meta = yaml.load(text.split(METADATA_SEP)[0], Loader=yaml.FullLoader)
            meta = Metadata(**meta, content_group=content_group)
        except Exception as e:
            logger.error(f"Couldn't parse metadata for '{path}'")
            logger.error(e)
            sys.exit(1)

        try:
            text_content = text.split(METADATA_SEP)[1]
            content = markdown(text_content)
        except IndexError:
            content = None

        return cls(meta, content)

    def render(self, jinja2_env, navbar):
        """writes html files to output directory"""
        template = jinja2_env.get_template(self.template_file)
        rendered_html = template.render(page=self, navbar=navbar)
        return rendered_html

    def __repr__(self):
        return f"Page({self.meta.title}, {self.html_path}, {self.template_file})"


class IndexPage(Page):
    def __init__(self, name: str, pages: list[Page], number: int):
        meta = Metadata(name, urlstub="index")
        self._items = pages
        self._number = number
        url = f"/{meta.title}/index{self._number + 1 if self._number > 0 else ''}.html"
        super().__init__(meta, url)

    @property
    def items(self):
        return self._items

    @property
    def number(self):
        return self._number

    def render(self, jinja2_env, paginator, navbar):
        template_name = f"index.html.jinja2"
        template = jinja2_env.get_template(template_name)
        rendered_html = template.render(index=self, children=self._items, paginator=paginator, navbar=navbar)
        return rendered_html
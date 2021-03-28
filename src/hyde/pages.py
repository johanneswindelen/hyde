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
    type: str
    urlstub: str
    draft: bool = False
    date: date = None
    author: str = None


class Page(object):
    def __init__(self, meta: Metadata, content: str):
        self.meta = meta
        self.content = content
        self._html_path = None

    @property
    def template_file(self):
        return f"{self.meta.type}.html.jinja2"

    @property
    def html_path(self):
        return self._html_path

    @property.setter
    def html_path(self, html_path: Path):
        self._html_path = html_path

    @property
    def url(self):
        return f"{self.meta.urlstub}.html"

    @classmethod
    def from_file(cls, path: Path):
        with open(path, "r") as f:
            text = f.read()
        try:
            meta = yaml.load(text.split(METADATA_SEP)[0], Loader=yaml.FullLoader)
            meta = Metadata(**meta)
        except Exception as e:
            logger.error(e)
            logger.warning(f"Couldn't parse metadata for '{path}'")
            sys.exit(1)

        try:
            text_content = text.split(METADATA_SEP)[1]
            content = markdown(text_content)
        except IndexError:
            content = None

        return cls(meta, content)

    def render_html(self, jinja2_env, template_kwargs):
        """writes html files to output directory"""
        template = jinja2_env.get_template(self.template_file)
        rendered_html = template.render(meta=self.meta, **template_kwargs)
        return rendered_html

    def __repr__(self):
        return f"Page({self.meta.title}, {self.html_path}, {self.template_file})"

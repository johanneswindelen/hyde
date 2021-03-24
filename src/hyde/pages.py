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
    is_index: bool = False
    draft: bool = False
    date: date = None
    author: str = None


class HydePage(object):
    def __init__(self, meta: Metadata, content: str):
        self.meta = meta
        self.content = content

    @property
    def template_file(self):
        if self.meta.is_index:
            return "index.html.jinja2"
        else:
            return f"{self.meta.type}.html.jinja2"

    @property
    def url(self):
        return str("/" / self.html_path)

    @property
    def html_path(self):
        if self.meta.is_index:
            return Path(f"{self.meta.type}/index.html")
        else:
            return Path(f"{self.meta.type}/{self.meta.urlstub}.html")

    @classmethod
    def from_dir(cls, directory: Path):
        t = directory.stem
        meta = Metadata(title=t.capitalize(), type="posts", urlstub="index", is_index=True)
        return cls(meta, None)

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
        return f"Hydepage({self.meta.title}, {self.html_path}, {self.template_file})"

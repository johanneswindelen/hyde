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
    urlstub: str = "index"
    draft: bool = False
    date: date = None
    author: str = None


@dataclass(init=False, repr=False)
class HydePage(object):
    meta: Metadata
    html_path: Path
    url: str
    content: str = None
    file_path: Path = None
    template_file: str = None

    def __init__(self, meta: Metadata, html_path: Path, content: str = None, file_path: Path = None):
        self.meta = meta
        self.html_path = html_path
        self.content = content
        self.file_path = file_path
        self.url = str("/" / html_path)
        self.template_file = f"{meta.type}.html.jinja2"

    @classmethod
    def from_dir(cls, directory: Path, html_path: Path):
        t = directory.stem
        meta = Metadata(title=t.capitalize(), type="index")
        return cls(meta, html_path)

    @classmethod
    def from_file(cls, path: Path, html_path: Path):
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

        return cls(meta, html_path, content, path)

    def render_html(self, jinja2_env, template_kwargs):
        """writes html files to output directory"""
        template = jinja2_env.get_template(self.template_file)
        rendered_html = template.render(meta=self.meta, **template_kwargs)
        return rendered_html

    def __repr__(self):
        return f"Hydepage({self.meta.title}, {self.html_path}, {self.template_file})"

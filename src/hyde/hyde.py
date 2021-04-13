import argparse
import os
import shutil
import sys
import logging
from pathlib import Path
from typing import Callable
import copy

import yaml
import jinja2

from hyde.server import HydeServer
from hyde.pages import ContentPage, Page
from hyde.paginator import Paginator
from hyde.errors import HydeError


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SCAFFOLDING_DIR = os.path.join(ROOT_DIR, "scaffolding")

TEMPLATE_DIR = "templates"
CONTENT_DIR = "content"
STATIC_DIR = "static"
OUTPUT_DIR = "output"
CONFIG_FILE = "config.yaml"

logging.basicConfig()
logger = logging.getLogger("Hyde")
logger.setLevel(logging.DEBUG)


class Hyde(object):
    def __init__(self):
        self.template_dir = Path(".").joinpath(TEMPLATE_DIR)
        self.content_dir = Path(".").joinpath(CONTENT_DIR)
        self.static_dir = Path(".").joinpath(STATIC_DIR)
        self.output_dir = Path(".").joinpath(OUTPUT_DIR)
        config_file_path = Path(".").joinpath(CONFIG_FILE)
        self.root_dir = Path(".")

        self.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
        )

    def _find_files(self, subdir: Path, filter_fn: Callable[[Path], bool]):
        """ Find files that match the given filter function in subdir """
        search_dir = self.root_dir.joinpath(subdir)
        matches = []
        for dirpath, dirnames, files in os.walk(search_dir):
            for f in files:
                if filter_fn(Path(f)):
                    matches.append(Path(dirpath).joinpath(f))
        return matches

    def __copy_static(self):
        dest_dir = self.output_dir.joinpath(STATIC_DIR)
        shutil.copytree(self.static_dir, dest_dir, dirs_exist_ok=True)

    def _sort_content_pages(self, content_pages: list[Page]) -> tuple[list[Page], dict[str, list[Page]]]:
        """ Sort content pages into those that are paginated and those that are not """
        paginated_content = {}
        unpaginated_content = []

        for page in content_pages:
            content_type = page.meta.template
            if content_type in ["posts", "snippets"]: # FIXME: this should probably be configurable. Need to add a config file
                try:
                    paginated_content[content_type].append(page)
                except (AttributeError, KeyError) as e:
                    paginated_content[content_type] = [page]
            else:
                unpaginated_content.append(page)
        return unpaginated_content, paginated_content

    def _write_content_to_file(self, content: str, path: Path):
        os.makedirs(path.parent, exist_ok=True)
        with open(path, "w") as fp:
            fp.write(content)

    def _render_content_to_html(self, single_pages, paginated_pages) -> list[tuple[str, Path]]:
        rendered_pages = []

        # Build navbar links
        navbar_pages = copy.deepcopy(single_pages)

        for content_type, pages in paginated_pages.items():
            paginator = Paginator(name=content_type, content=pages)
            index = next(paginator)
            navbar_pages.append(index)

        # All content that's not paginated is accessible via the navigation bar.
        # Render and write pages required for navigation links.
        for page in single_pages:
            page_html = page.render(self.jinja2_env, nav_bar_pages=navbar_pages)
            rendered_pages.append((page_html, page.html_path))

        # Render and write paginated pages 
        for content_type, pages in paginated_pages.items():
            paginator = Paginator(name=content_type, content=pages)

            for index in paginator:
                index_html = index.render(self.jinja2_env, paginator, nav_bar_pages=navbar_pages)
                rendered_pages.append((index_html, index.html_path))

                for page in index.items:
                    page_html = page.render(self.jinja2_env, nav_bar_pages=navbar_pages)
                    rendered_pages.append((page_html, page.html_path))
                    
        return rendered_pages

    def generate(self):
        self.check()

        # remove previous output directory if it exists
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

         # find all content files and instantiate them into Pages
        content_files = self._find_files(self.content_dir, lambda x: x.suffix == ".md")
        content_pages = [ContentPage.from_file(f) for f in content_files]

        # sort content into pages reachable through a paginator (such as blog posts)
        # and pages available through the website navigation links (about, contact, home)
        navbar_content, paginated_content = self._sort_content_pages(content_pages)

        # instantiate pages and render HTML
        rendered_pages = self._render_content_to_html(navbar_content, paginated_content)

        # write rendered HTML to files
        for html, html_path in rendered_pages:
            html_path = self.output_dir / html_path
            self._write_content_to_file(html, html_path)

        # copy static assets
        self.__copy_static()

    def check(self):
        checks = []
        if not os.path.isdir(self.template_dir):
            checks.append(f"\tproject is missing the '{TEMPLATE_DIR}' directory")
        if not os.path.isdir(self.content_dir):
            checks.append(f"\tproject is missing the '{CONTENT_DIR}' directory")
        
        if len(checks) > 0:
            raise HydeError(
                f"It appears that '{self.root_dir}' is not a valid Hyde project. The following errors were encountered:",
                "\n".join(checks),
            )

    @staticmethod
    def new_site(project_dir):
        curr_dir = os.getcwd()
        base_path = os.path.join(curr_dir, project_dir, "")

        logger.info(f"Creating a new Hyde project at {base_path}")

        # Create directories for new project
        try:
            os.makedirs(base_path)
        except FileExistsError:
            logger.error(f"There's already a directory at {base_path}. Aborting!")
            sys.exit(1)

        # Copy template files over
        shutil.copytree(SCAFFOLDING_DIR, base_path, dirs_exist_ok=True)

        logger.info(f"Done!")


def cli():
    parser = argparse.ArgumentParser(
        prog="hyde", description="A pytastic static website generator"
    )
    subparsers = parser.add_subparsers(title="Available subcommands", dest="subcommand")

    parser_new = subparsers.add_parser("new", help="create a new Hyde website")
    parser_new.add_argument(
        "directory", help="directory to create Hyde website template"
    )

    parser_serve = subparsers.add_parser("serve", help="serve Hyde website locally")
    parser_serve.add_argument("-p", "--port", help="port to serve on", default=8000)

    _ = subparsers.add_parser("gen", help="generate static html sites")

    args = parser.parse_args()

    # determine what subcommand has been called
    if args.subcommand == "new":
        Hyde.new_site(args.directory)
    if args.subcommand == "serve":
        h = Hyde()
        h.generate()
        s = HydeServer(h.output_dir, h.root_dir, h.generate)
        s.serve(port=args.port)
    if args.subcommand == "gen":
        h = Hyde()
        h.generate()

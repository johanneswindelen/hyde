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

    def _sort_content_pages(self, content_pages: list[Page]) -> tuple[list[Page], dict[str, list[Page]]]:
        """ Sort content pages into those that are paginated and those that are not """
        paginated_content = {}
        unpaginated_content = []

        for page in content_pages:
            if (content_group := page.meta.content_group) is not None:
                try:
                    paginated_content[content_group].append(page)
                except (AttributeError, KeyError) as e:
                    paginated_content[content_group] = [page]
            else:
                unpaginated_content.append(page)
        return unpaginated_content, paginated_content

    def _write_content_to_file(self, content: str, path: Path):
        os.makedirs(path.parent, exist_ok=True)
        with open(path, "w") as fp:
            fp.write(content)

    def _render_navbar_html(self, single_pages, paginated_pages):
        # Build navbar links
        navbar_pages = copy.deepcopy(single_pages)

        for content_type, pages in paginated_pages.items():
            paginator = Paginator(name=content_type, content=pages)
            index = next(paginator)
            navbar_pages.append(index)

        nav_template = self.jinja2_env.get_template("navbar.html.jinja2")
        return nav_template.render(nav_bar_pages=navbar_pages)

    def _render_content_to_html(self, single_pages, paginated_pages, navbar_html) -> list[tuple[str, Path]]:
        rendered_pages = []

        # All content that's not paginated is accessible via the navigation bar.
        # Render and write pages required for navigation links.
        for page in single_pages:
            page_html = page.render(self.jinja2_env, navbar=navbar_html)
            rendered_pages.append((page, page_html))

        # Render and write paginated pages 
        for content_type, pages in paginated_pages.items():
            paginator = Paginator(name=content_type, content=pages)

            for index in paginator:
                index_html = index.render(self.jinja2_env, paginator, navbar=navbar_html)
                rendered_pages.append((index, index_html))

                for page in index.items:
                    page_html = page.render(self.jinja2_env, navbar=navbar_html)
                    rendered_pages.append((page, page_html))
        
        logger.debug(f"Rendered a total of {len(rendered_pages)} pages.")
        for p in rendered_pages:
            logger.debug(f"\t{p[0]}")

        return rendered_pages

    def generate(self):
        self.check()

        # remove previous output directory if it exists
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

         # find all content files and instantiate them into Pages
        content_files = self._find_files(self.content_dir, lambda x: x.suffix == ".md")
        media_files = self._find_files(self.content_dir, lambda x: x.suffix in [".jpeg"])
        content_pages = [ContentPage.from_file(f, self.content_dir) for f in content_files]

        public_content_pages = copy.deepcopy(content_pages)
        public_content_pages = list(filter(lambda x: x.meta.content_group != "_private", public_content_pages))
        public_media_files = list(filter(lambda x: "_private" in x.parts, media_files))

        self._write_website(public_content_pages, public_media_files)

        for stem in ["testing123"]:
            p_content_pages = self._set_new_content_root(stem, content_pages)
            self._write_website(p_content_pages, media_files)

        # copy static assets
        dest_dir = self.output_dir.joinpath(STATIC_DIR)
        shutil.copytree(self.static_dir, dest_dir, dirs_exist_ok=True)        

    def _set_new_content_root(self, root, content_pages):
        n_content_pages = copy.deepcopy(content_pages)
        for p in n_content_pages:
            p.url = f"/{root}{p.url}"
        return n_content_pages

    def _write_website(self, content_pages, media_files):
        # sort content into pages reachable through a paginator (such as blog posts)
        # and pages available through the website navigation links (about, contact, home)
        unpaginated_content, paginated_content = self._sort_content_pages(content_pages)

        # generate navbar snippet
        navbar_html = self._render_navbar_html(unpaginated_content, paginated_content)

        # instantiate pages and render HTML
        rendered_pages = self._render_content_to_html(unpaginated_content, paginated_content, navbar_html)

        # write rendered HTML to files
        for page, html in rendered_pages:
            html_path = self.output_dir / page.html_path
            self._write_content_to_file(html, html_path)

        # for src, dst in media_files:
        #     shutil.copy(src, dst)

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

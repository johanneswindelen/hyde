import argparse
import os
import shutil
import sys
import logging
from pathlib import Path

import yaml
import jinja2

from hyde.server import HydeServer
from hyde import config
from hyde.pages import Page
from hyde.paginator import Paginator
from hyde.errors import HydeValidationError, HydeError


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
        self.config_file_path = Path(".").joinpath(CONFIG_FILE)
        self.root_dir = Path(".")

        self.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
        )

    def __find_files(self, subdir, filter_fn):
        """find files that match the given filter function in subdir"""
        search_dir = os.path.join(self.root_dir, subdir)
        matches = []
        for dirpath, dirnames, files in os.walk(search_dir):
            for f in files:
                if filter_fn(f):
                    matches.append(Path(os.path.join(dirpath, f)))
        return matches

    def __copy_static(self):
        dest_dir = self.output_dir.joinpath(STATIC_DIR)
        shutil.copytree(self.static_dir, dest_dir, dirs_exist_ok=True)

    def __sort_content_pages(self, content_pages: list[Page]) -> tuple[list[Page], dict[str, list[Page]]]:
        pass

    def __write_file(self, content: str, path: Path):
        os.makedirs(path.parent, exist_ok=True)
        with open(path, "w") as fp:
            fp.write(content)

    def generate(self):
        self.check()

        # remove previous output directory if it exists
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

        # find all content files and instantiate them into Pages
        content_files = self.__find_files(self.content_dir, lambda x: x.endswith(".md"))
        content_pages = [Page.from_file(f) for f in content_files]

        # sort content into pages reachable through a paginator (such as blog posts)
        # and pages available through the website navigation links (about, contact, home)
        content_pages_for_pagination, content_pages_on_root = self.__sort_content_pages(content_pages)

        # render pages required for navigation links
        for page in content_pages_on_root:
            page.html_path = Path(page.url)
            page_html = page.render_html(self.jinja2_env)
            self._write_file(page_html, page.html_path)

        # render pages 
        for content_type, pages in content_pages_for_pagination.items():
            paginator = Paginator(name=content_type, pages=pages)

            for index in paginator:
                index_html = index.render_html(self.jinja2_env, paginator)
                self._write_file(index_html, index.html_path)

                for page in index.pages:
                    # set the page html_path attribute, as the full path is only
                    # known once a page has been loaded by a paginator
                    page.html_path = Path(index.url).joinpath(page.url)
                    page_html = page.render_html(self.jinja2_env)
                    self._write_file(page_html, page.html_path)

        # copy static assets
        self.__copy_static()

    @staticmethod
    def print_errors(errors):
        logger.error("Hyde ran into errors when generating your website.")
        for e in errors:
            logger.error(f"{e[0]}: {e[1]}")

    def check(self):
        checks = []
        if not os.path.isdir(self.template_dir):
            checks.append(["E", f"project is missing the '{TEMPLATE_DIR}' directory"])
        if not os.path.isdir(self.content_dir):
            checks.append(["E", f"project is missing the '{CONTENT_DIR}' directory"])
        if not os.path.isfile(self.config_file_path):
            checks.append(["E", f"project is missing the '{CONFIG_FILE}' file"])
        else:
            with open(self.config_file_path) as f:
                project_config = yaml.load(f, Loader=yaml.FullLoader)
            try:
                if "site-name" not in project_config.keys():
                    checks.append(
                        [
                            "E",
                            "project configuration file is missing required 'site-name' key",
                        ]
                    )
                if "base-url" not in project_config.keys():
                    checks.append(
                        [
                            "E",
                            "project configuration file is missing required 'base-url' key",
                        ]
                    )
            except AttributeError:
                checks.append(
                    ["E", "the project configuration file appears to be invalid YAML."]
                )

        if len(checks) > 0:
            raise HydeValidationError(
                f"It appears that '{self.root_dir}' is not a valid Hyde project. The following errors were encountered:",
                checks,
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
        shutil.copytree(config.SCAFFOLDING_DIR, base_path, dirs_exist_ok=True)

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

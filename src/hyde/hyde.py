import argparse
import os
import shutil
import sys
import logging
from pathlib import Path

import yaml
import jinja2
from anytree import Node, RenderTree, Resolver, LevelOrderIter

from hyde.server import HydeServer
from hyde import config
from hyde.pages import HydePage
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

    def __build_site_tree(self) -> Node:
        root = Node(self.content_dir)
        r = Resolver("name")
        for base, dirs, files in os.walk(self.content_dir):
            parent = r.get(root, "/" + base)
            for d in dirs:
                directory = Path(base).joinpath(d)
                _ = Node(d, parent=parent, data=HydePage.from_dir(directory))
            for f in filter(lambda x: x.endswith(".md"), files):
                content_file = Path(base).joinpath(f)
                _ = Node(f, parent=parent, data=HydePage.from_file(content_file))
        logger.info(RenderTree(root))
        return root

    def __validate_tree(self, tree):
        pass

    def __copy_static(self):
        dest_dir = self.output_dir.joinpath(STATIC_DIR)
        shutil.copytree(self.static_dir, dest_dir, dirs_exist_ok=True)

    def generate(self):
        self.check()

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

        tree = self.__build_site_tree()
        self.__validate_tree(tree)
        indices = [p.data for p in LevelOrderIter(tree)
                   if not p.is_root and p.data.meta.type == "index"]

        for n in LevelOrderIter(tree, filter_=lambda node: not node.is_root):
            page = n.data
            try:
                template_args = {
                    "page": page,
                    "indices": indices
                }
                if n.children:
                    template_args["children"] = [c.data for c in n.children]
                print(f"{page} -> {template_args}")
                rendered_page = page.render_html(self.jinja2_env, template_args)
            except jinja2.exceptions.TemplateNotFound:
                logger.error(f"E: Couldn't find template '{page.template_file}' "
                             f"required to render '{page}'")
                sys.exit(1)
            except jinja2.exceptions.UndefinedError as e:
                logger.error(f"Missing template argument for node '{n.name}', "
                             f"template '{page.template_file}':\n{e}")
                sys.exit(1)

            path = self.output_dir.joinpath(page.html_path)
            print(f"writing {page} to {path}")

            os.makedirs(path.parent, exist_ok=True)

            with open(path, "w") as f:
                f.write(rendered_page)

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

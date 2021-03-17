import argparse
import os
import pathlib
import shutil
import sys
import http.server
import socketserver

import yaml
import jinja2
from markdown import markdown

from hyde.server import HydeServer
from hyde import config


TEMPLATE_DIR = "templates"
CONTENT_DIR = "content"
STATIC_DIR = "static"
OUTPUT_DIR = "output"
CONFIG_FILE = "config.yaml"


class ValidationError(Exception):
    """An Exception type that holds a list of validation errors"""

    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

    def __str__(self):
        errors = [f"\t{level}: {err}" for level, err in self.errors]
        return "\n".join(errors)


class Hyde(object):
    def __init__(self):
        project_dir = os.getcwd()

        self.template_dir = os.path.join(project_dir, TEMPLATE_DIR)
        self.content_dir = os.path.join(project_dir, CONTENT_DIR)
        self.static_dir = os.path.join(project_dir, STATIC_DIR)
        self.output_dir = os.path.join(project_dir, OUTPUT_DIR)
        self.config_file_path = os.path.join(project_dir, CONFIG_FILE)
        self.root_dir = project_dir

        try:
            Hyde.check(
                self.root_dir,
                self.template_dir,
                self.content_dir,
                self.output_dir,
                self.config_file_path,
            )
        except ValidationError as e:
            self.__exit(
                f"'{project_dir}' does not appear to be a Hyde project.\n{e.errors}"
            )

        self.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
        )

    def __exit(self, msg, exc=None, retval=1):
        print(msg)
        if exc is not None:
            print(exc, exc_info=True)
        sys.exit(retval)

    def __find_files(self, subdir, filter_fn):
        """find files that match the given filter function in subdir"""
        search_dir = os.path.join(self.root_dir, subdir)
        matches = []
        for dirpath, dirnames, files in os.walk(search_dir):
            for f in files:
                if filter_fn(f):
                    matches.append(os.path.join(dirpath, f))
        return matches

    def __parse_content(self):
        """validates hyde content for correctness"""
        files = self.__find_files("content", lambda x: x.endswith(".md"))

        content = {}
        for f in files:
            meta, c = self.__parse_file(f)
            content[meta["title"]] = [meta, c]
        return content

    def __parse_file(self, c):
        with open(c, "r") as f:
            text = f.read()

        header, body = text.split("---")[0:2]

        meta = yaml.load(header, Loader=yaml.FullLoader)

        if not all(k in meta for k in ["author", "date", "draft", "type", "title"]):
            raise Exception("Missing metadata key in header!")

        content = markdown(body)

        return meta, content

    def __generate_html_pages(self, content):
        """writes html files to output directory"""
        html_pages = []
        for (title, c) in content.items():
            if c[0]["type"] == "post":
                template = self.jinja2_env.get_template("posts.html.jinja2")
            if c[0]["type"] == "snippet":
                template = self.jinja2_env.get_template("posts.html.jinja2")
            if c[0]["type"] == "home":
                template = self.jinja2_env.get_template("home.html.jinja2")

            sanitized_title = "-".join(c[0]["title"].split(" ")).lower()
            html_filename = os.path.join(c[0]["type"], sanitized_title + ".html")
            html_pages.append(
                {
                    "path": html_filename,
                    "title": c[0]["title"],
                    "html": template.render(meta=c[0], content=c[1]),
                }
            )
        return html_pages

    def __generate_html_index(self, pages):
        template = self.jinja2_env.get_template("index.html.jinja2")
        content = []
        for p in pages:
            content.append({"title": p["title"], "path": p["path"]})

        pages.append(
            {
                "path": "index.html",
                "title": "Home",
                "html": template.render(title="Index", content=content),
            }
        )

        return pages

    def __write_html(self, pages):
        # generate content pages
        for p in pages:
            html_path = os.path.join(self.output_dir, p["path"])
            os.makedirs(pathlib.Path(html_path).parent.absolute(), exist_ok=True)
            with open(html_path, "w") as f:
                f.write(p["html"])

    def __copy_static(self):
        dest_dir = os.path.join(self.output_dir, "static")
        shutil.copytree(self.static_dir, dest_dir, dirs_exist_ok=True)

    def generate(self):
        content = self.__parse_content()
        pages = self.__generate_html_pages(content)
        pages = self.__generate_html_index(pages)
        self.__write_html(pages)
        self.__copy_static()

    @staticmethod
    def check(root_dir, template_dir, content_dir, output_dir, config_file_path):
        checks = []
        if not os.path.isdir(template_dir):
            checks.append(["E", f"project is missing the '{TEMPLATE_DIR}' directory"])
        if not os.path.isdir(content_dir):
            checks.append(["E", f"project is missing the '{CONTENT_DIR}' directory"])
        if not os.path.isfile(config_file_path):
            checks.append(["E", f"project is missing the '{CONFIG_FILE}' file"])
        else:
            with open(config_file_path) as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
            try:
                if not "site-name" in config.keys():
                    checks.append(
                        [
                            "E",
                            "project configuration file is missing required 'site-name' key",
                        ]
                    )
                if not "base-url" in config.keys():
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
            raise ValidationError(
                f"It appears that '{root_dir}' is not a valid Hyde project. The following errors were encountered:",
                checks,
            )

    @staticmethod
    def new_site(project_dir):
        curr_dir = os.getcwd()
        base_path = os.path.join(curr_dir, project_dir, "")

        print(f"Creating a new Hyde project at {base_path}")

        # Create directories for new project
        try:
            os.makedirs(base_path)
        except FileExistsError:
            print(f"There's already a directory at {base_path}. Aborting!")
            sys.exit(1)

        # Copy template files over
        shutil.copytree(config.SCAFFOLDING_DIR, base_path, dirs_exist_ok=True)

        print(f"Done!")


def cli():
    parser = argparse.ArgumentParser(
        prog="hyde", description="A pytastic static website generator"
    )
    subparsers = parser.add_subparsers(title="Available subcommands", dest="subcommand")

    parser_new = subparsers.add_parser("new", help="create a new Hyde website")
    parser_new.add_argument(
        "directory", help="directory to create Hyde website template"
    )

    parser_check = subparsers.add_parser(
        "check", help="checks if the current directory is a valid Hyde project"
    )
    parser_check.add_argument(
        "-d",
        "--directory",
        help="specify a hyde project directory instead of using the current one",
        default=os.getcwd(),
    )

    parser_serve = subparsers.add_parser("serve", help="serve Hyde website locally")
    parser_serve.add_argument("-p", "--port", help="port to serve on", default=8000)

    parser_gen = subparsers.add_parser("gen", help="generate static html sites")

    args = parser.parse_args()

    # determine what subcommand has been called
    if args.subcommand == "new":
        Hyde.new_site(args.directory)
    if args.subcommand == "check":
        Hyde.check(args.directory)
    if args.subcommand == "serve":
        h = Hyde()
        h.generate()
        s = HydeServer(h.output_dir, h.root_dir, h.generate)
        s.serve(port=args.port)

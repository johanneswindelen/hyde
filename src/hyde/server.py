""" HydeServer

This file contains the HydeServer and associated classes. The HydeServer provides
a server to locally serve your static site.

The FileChangedFunctionHandler is used in conjunction with the `watchdog` package
to regenerate the site as the files inside the hyde project are edited.
"""
import http.server
import socketserver
from collections.abc import Callable
from pathlib import Path
import os

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer


class FileChangedFunctionHandler(RegexMatchingEventHandler):
    """ A watchdog handler that calls a given function when changes are detected. """
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        super().__init__(*args, **kwargs)

    def on_any_event(self, event):
        print(f"Filesystem changed, re-generating!")
        self.fn()


class HydeServer(object):
    """ Development server for a hyde project """
    def __init__(self, serve_dir: Path, root_dir: Path, on_change: Callable[[], None]):
        """
        :param serve_dir: path to directory to serve HTML files from
        :param root_dir: path to the root of the hyde project
        :param on_change: function to call on filesystem changes
        """
        self.serve_dir = serve_dir
        self.root_dir = root_dir
        self.fs_handler = FileChangedFunctionHandler(
            on_change,
            regexes=[r".*\.[jinja2|html|css|md|yaml]"],
            ignore_regexes=[r".*/output/.*"],
            ignore_directories=True,
        )

    def __get_request_handler(self, *args, **kwargs):
        """
        Overwrite the 'directory' parameter when instantiating the
        SimpleHTTPRequestHandler, which defaults to current working
        directory.

        :param args: passed through to SimpleHTTPRequestHandler
        :param kwargs: passed through to SimpleHTTPRequestHandler
        :return: SimpleHTTPRequestHandler instance
        """
        kwargs.pop("directory", None)
        return http.server.SimpleHTTPRequestHandler(
            *args, **kwargs, directory=self.serve_dir
        )

    def serve(self, ip_addr="127.0.0.1", port=8000):
        """
        Start the HydeServer.

        :param port: port number to run the server on.
        :param ip_addr: IP address to run the server on.
        :return: None
        """

        # start filesystem observer watching the root directory for any file changes
        # and regenerating the output directory when changes occur.
        observer = Observer()
        observer.schedule(self.fs_handler, self.root_dir, recursive=True)
        observer.start()

        print(f"Started filesystem watcher on '{self.root_dir}'.")
        print("Site will be updates as you make changes to your files.")

        try:
            # allow_reuse_address prevents 'OSError: [Errno 48] Address already in use'
            # which occurs when restarting the server after having viewed a page in a browser
            # (on MacOS 11 and using Safari, maybe others).
            socketserver.TCPServer.allow_reuse_address = True
            httpd = socketserver.TCPServer((ip_addr, port), self.__get_request_handler)

            print(f"Serving Hyde page at http://127.0.0.1:{port}")
            print(f"Press Ctrl-C to stop...")

            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

        observer.stop()
        httpd.shutdown()
        httpd.server_close()
        observer.join()

import http.server
import socketserver
from collections.abc import Callable
from pathlib import Path

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


class FileChangedFunctionHandler(PatternMatchingEventHandler):
    def __init__(self, fn, **kwargs):
        self.fn = fn
        super().__init__(**kwargs)

    def on_any_event(self, _):
        print(f"Filesystem changed, re-generating!")
        self.fn()


class HydeServer(object):
    def __init__(self, serve_dir: Path, root_dir: Path, on_change: Callable[[], None]):
        self.serve_dir = serve_dir
        self.root_dir = root_dir
        self.fs_handler = FileChangedFunctionHandler(
            on_change,
            patterns=["*.jinja2", "*.html", "*.css", "*.md", "*.yaml"],
            ignore_patterns=[],
            ignore_directories=False,
        )

    def serve(self, port=8000):
        def handler(*args, **kwargs):
            # Overwrite the default SimpleHTTPRequestHandler behavior, which is to serve
            # the current working directory.
            kwargs.pop("directory", None)
            return http.server.SimpleHTTPRequestHandler(
                *args, **kwargs, directory=self.serve_dir
            )

        try:
            # start filesystem observer watching the root directory for any file changes
            # and regenerating the output directory when changes occur.
            observer = Observer()
            observer.schedule(self.fs_handler, self.root_dir, recursive=True)
            observer.start()
            print(
                f"Started filesystem watcher on '{self.root_dir}', site will be updates as you make changes to your files."
            )

            # allow_reuse_address prevents 'OSError: [Errno 48] Address already in use'
            # which occurs when restarting the server after having viewed a page in a browser
            # (on MacOS 11 and using Safari, maybe others).
            socketserver.TCPServer.allow_reuse_address = True
            httpd = socketserver.TCPServer(("", port), handler)
            print(f"Serving Hyde page at http://127.0.0.1:{port}")
            print(f"Press Ctrl-C to stop...")
            httpd.serve_forever()

        except KeyboardInterrupt:
            observer.stop()
            httpd.shutdown()
            httpd.server_close()
            observer.join()

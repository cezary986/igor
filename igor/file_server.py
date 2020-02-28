import http.server
import socketserver
import os
from threading import Thread


class FileServerProcess(Thread):
    def __init__(self, port=8000, root_directory=None):
        """
        :param port: server port
        :param root_directory: root directory from which server will serve files, if None it will be system root dir
        """
        self.port = port
        self.root_directory = root_directory
        Thread.__init__(self)

    def run(self):
        root_directory = self.root_directory

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                if root_directory is None:
                    current_path = os.path.dirname(os.path.realpath(__file__))
                    root_system_path = current_path.split('\\')[0] + '/'
                super().__init__(*args, directory=root_directory, **kwargs)

            def translate_path(self, path):
                path = path.replace(root_directory, '')
                path = http.server.SimpleHTTPRequestHandler.translate_path(self, path)
                return path

            def do_POST(self):
                length = self.headers['content-length']
                data = self.rfile.read(int(length))
                with open(self.path[1:], 'wb') as fh:
                    fh.write(data)

                self.send_response(200)

        with socketserver.TCPServer(("", self.port), Handler) as httpd:
            httpd.serve_forever()


def run_file_server(port=8080, root_directory=None):
    thread = FileServerProcess(port, root_directory)
    thread.deamon = True
    thread.start()

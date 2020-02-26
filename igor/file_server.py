import http.server
import socketserver
import os
from threading import Thread


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        curent_path = os.path.dirname(os.path.realpath(__file__))
        root_system_path = curent_path.split('\\')[0] + '/'
        self.directory = root_system_path
        super().__init__(*args, directory=self.directory, **kwargs)

    def translate_path(self, path):
        path = path.replace(self.directory, '')
        path = http.server.SimpleHTTPRequestHandler.translate_path(self, path)
        return path

    def do_POST(self):
        length = self.headers['content-length']
        data = self.rfile.read(int(length))
        with open(self.path[1:], 'wb') as fh:
            fh.write(data)

        self.send_response(200)


class FileServerProcess(Thread):
    def __init__(self, port=8000):
        self.port = port
        Thread.__init__(self)

    def run(self):
        with socketserver.TCPServer(("", self.port), Handler) as httpd:
            httpd.serve_forever()


def run_file_server(port=8080):
    thread = FileServerProcess(port)
    thread.deamon = True
    thread.start()

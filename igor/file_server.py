import http.server
import socketserver
import os
from threading import Thread


def HandlerFactory(root_directory):

    class Handler(http.server.SimpleHTTPRequestHandler):

        def __init__(self, *args, **kwargs):
            self.root_directory = root_directory
            if self.root_directory is None:
                current_path = os.path.dirname(os.path.realpath(__file__))
                root_system_path = current_path.split('\\')[0] + '/'
                self.root_directory = root_system_path
            super().__init__(*args, directory=self.root_directory, **kwargs)

        def translate_path(self, path):
            path = path.replace(root_directory, '')
            path = http.server.SimpleHTTPRequestHandler.translate_path(self, path)
            return path

        def do_POST(self):
            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            with open(self.path[1:], 'wb') as fh:
                fh.write(data)
            response = bytes('{"message": "File saved."}', "utf-8")
            self.send_response(200)
            self.send_header("Content-Length", str(len(response)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response)

        def do_OPTIONS(self):
            self.send_response(200, "ok")
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
            response = bytes('', "utf-8")
            self.end_headers()
            self.wfile.write(response)

    return Handler


class FileServerProcess(Thread):
    def __init__(self, port=8000, root_directory=None):
        """
        :param port: server port
        :param root_directory: root directory from which server will serve files, if None it will be system root dir
        """
        self.port = port
        self.httpd = None
        self.root_directory = root_directory
        Thread.__init__(self)

    def run(self):
        handlerClass = HandlerFactory(self.root_directory)

        self.httpd = socketserver.TCPServer(("", self.port), handlerClass)
        self.httpd.serve_forever()
    
    def kill(self):
        self.httpd.shutdown()


def run_file_server(port=8080, root_directory=None):
    thread = FileServerProcess(port, root_directory)
    thread.deamon = True
    thread.start()
    return thread

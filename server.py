import graph.loadGraph
import graph.path

import http.server
import json
import re

WEB_APP_PATH = 'webapp'

PORT = 9090
# PORT = 17263

# Note that we are extending SimeplHTTPRequestHandler (which serves static files)
# instead of BaseHTTPRequestHandler (which does nothing).
# The the route is to the webapp, we will pass the call down to the superclass.
# Otherwise, we will serve normally.
class GraphHandler(http.server.SimpleHTTPRequestHandler):
    _graph = graph.loadGraph.fetchGraph()
    _entities = graph.loadGraph.fetchEntities()
    _bareEntities = graph.loadGraph.fetchBareEntities()

    def do_GET(self):
        # TEST
        print(self.path)

        if (self.path.startswith('/' + WEB_APP_PATH) or self.path == '/favicon.ico'):
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

        if (self.path == '/api/entities'):
            self._getBareEntities()
            return

        if (self.path.startswith('/api/path/')):
            match = re.search(r'^/api/path/(\d+)/(\d+)/(\d+)/?$', self.path)
            if (match == None):
                self.send_response(404)
                self.wfile.write(bytes('', "utf8"))
                return

            startId = int(match.group(1))
            endId = int(match.group(2))
            numPaths = int(match.group(3))

            self._getPaths(startId, endId, numPaths)
            return

    def _getBareEntities(self):
        # Send status and headers
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()

        self.wfile.write(bytes(json.dumps(GraphHandler._bareEntities), "utf8"))

    def _getPaths(self, startId, endId, numPaths):
        # Send status and headers
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()

        paths, edgeInfo, nodes = graph.path.findPaths(startId, endId, numPaths, GraphHandler._graph, GraphHandler._entities)
        content = {
            'paths': paths,
            'edgeInfo': edgeInfo,
            'nodes': nodes
        }

        self.wfile.write(bytes(json.dumps(content), "utf8"))

def runServer():
    print('Starting graph server...')

    # server_address = ('127.0.0.1', PORT)
    server_address = ('0.0.0.0', PORT)
    httpd = http.server.HTTPServer(server_address, GraphHandler)

    print('Running graph server...')

    httpd.serve_forever()

if __name__ == '__main__':
    runServer()

import http.server
import socketserver
import json
PORT = 8000

with open("all_nodes.json", "r") as f:
    all_nodes = json.loads(f.read())

class Handler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        p2 = self.path[1:]
        if p2 in all_nodes:
            print("node")
            print(p2)
            goal_s = json.dumps({"goal": p2})
            with open("goal.json", "w") as f:
                f.write(goal_s)
        super().do_GET()

#Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()


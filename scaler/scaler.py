from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import docker
import time

client = docker.from_env()
class ScaleHandler(BaseHTTPRequestHandler):
    threshold=5
    def read_backend_ips(self, filename):
        with open(filename, 'r') as file:
            ips = file.read().splitlines()
        return ips
    def remove_ip_from_file(self,ip_address, filename):
        # Read the contents of the file
        with open(filename, 'r') as file:
            lines = file.readlines()

        # Remove the specified IP address from the list of lines
        lines = [line.strip() for line in lines if line.strip() != ip_address]

        # Rewrite the modified contents back to the file
        with open(filename, 'w') as file:
            file.write('\n'.join(lines))
    def add_ip_to_file(self,ip_address, filename):
        # Open the file in append mode and write the IP address
        with open(filename, 'a') as file:
            file.write('\n'+ip_address)

    def do_GET(self):
        url_parts = urlparse(self.path)
        query_params = parse_qs(url_parts.query)
        
        container_no = query_params.get('conatiner_no', [''])[0]
        scale= query_params.get('scale', [''])[0]
        print(scale)
        if scale=="up":
            container = client.containers.run('app', detach=True, name=f"app{container_no}")
            while True:
                time.sleep(1)
                container=client.containers.get(f"app{container_no}")
                if container.status=="running":
                    break
            ip = container.attrs['NetworkSettings']['IPAddress']
        else:
            container = client.containers.get(f"app{container_no}")
            ip = container.attrs['NetworkSettings']['IPAddress']
            container.stop()
            container.remove()
            

        # ips = self.read_backend_ips('backendips.txt')
        # no_of_req_ser = int(count_value) 
        # if no_of_req_ser == 0:
        #     no_of_req_ser=1
        
        # no_of_ser=len(ips)

        # print(no_of_ser,no_of_req_ser)
        # if no_of_req_ser > no_of_ser:
        #     for i in range(no_of_req_ser-no_of_ser):
        #         container = client.containers.run('app', detach=True, name=f"app{i+1+no_of_ser}")
        #         container.reload()
        #         time.sleep(10)
        #         ip = container.attrs['NetworkSettings']['IPAddress']
        #         self.add_ip_to_file(ip,'backendips.txt')

        # elif no_of_req_ser < no_of_ser:
        #     for i in range(no_of_ser-no_of_req_ser):
                # container = client.containers.get(f"app{no_of_ser-i}")
                # ip = container.attrs['NetworkSettings']['IPAddress']
        #         self.remove_ip_from_file(ip,'backendips.txt')
        #         container.stop()
        #         container.remove()

        # Print the count value
        # print("Count value:", count_value) 
        print(ip)       
        self.send_response(200)
        self.end_headers()
        self.wfile.write(ip.encode())

server = HTTPServer(('0.0.0.0', 5001), ScaleHandler)
server.serve_forever()


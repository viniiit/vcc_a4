from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import random
from collections import deque
from datetime import datetime, timedelta
from collections import defaultdict
from socketserver import ThreadingMixIn
import threading
import time

ips=[[]]
class SlidingWindowRequestCounter:
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.request_timestamps = deque()
        self.count = 0
    def remove_req(self):
        timestamp = datetime.now()
        while self.request_timestamps and self.request_timestamps[0][0] < timestamp - timedelta(seconds=self.window_size):
            _, expired_count = self.request_timestamps.popleft()
            self.count -= expired_count
    
    def record_request(self, count, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        self.count += count
        self.request_timestamps.append((timestamp, count))
        while self.request_timestamps and self.request_timestamps[0][0] < timestamp - timedelta(seconds=self.window_size):
            _, expired_count = self.request_timestamps.popleft()
            self.count -= expired_count

    def get_request_count(self):
        return self.count

request_counter = SlidingWindowRequestCounter()
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass



class LoadBalancerHandler(BaseHTTPRequestHandler):
    container_no=2


    def do_GET(self):
        app=ips[0]
        min_con=ips[0][1]
        
        for ip_subarray in ips:
            if ip_subarray[1] < min_con:
                app=ip_subarray
        
        app[1]+=1
        app_ip=app[0]
        request_counter.record_request(1)
        response = requests.get(f"http://{app_ip}:5000/").text
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())

class ResetCountThread(threading.Thread):
    def run(self):
        while True:
            for ip_subarray in ips:
                ip_subarray[1]=0
            time.sleep(10)

class FileUpdaterThread(threading.Thread):
    def run(self):
        threshold=5
        container_no=2
        while True:
            time.sleep(2)
            request_counter.remove_req()
            
            total_in_window=request_counter.get_request_count()
            no_of_ser=len(ips)
            no_of_req_ser = int(int(total_in_window)/threshold) + 1
            if no_of_req_ser == 0:
                no_of_req_ser=1 
            print("total",total_in_window,"req",no_of_req_ser,"ser",no_of_ser)
            print(ips)
            if no_of_req_ser > no_of_ser:
                ip_new=requests.get(f"http://172.17.0.1:5001/?conatiner_no={container_no}&scale=up").text
                ips.append([ip_new,0])
                container_no+=1
            elif no_of_req_ser < no_of_ser:
                container_no-=1
                ip_new=requests.get(f"http://172.17.0.1:5001/?conatiner_no={container_no}&scale=down").text
                for ip_subarray in ips:
                    if ip_subarray[0] == ip_new:
                        ips.remove(ip_subarray)
            
def init_balancer():
    
    

    with open("backendips.txt", 'w') as file:
        pass

    ip_new = requests.get(f"http://0.0.0.0:5001/?conatiner_no={1}&scale=up").text
    ips.remove([])
    ips.append([ip_new,0])
    # Start the thread for updating the file
    file_updater_thread = FileUpdaterThread()
    file_updater_thread.start()

    reset_count_thread = ResetCountThread()
    reset_count_thread.start()

init_balancer()
server = ThreadingHTTPServer(('0.0.0.0', 8080), LoadBalancerHandler)
server.serve_forever()

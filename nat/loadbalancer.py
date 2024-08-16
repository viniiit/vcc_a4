import subprocess
import datetime

from collections import defaultdict
from collections import deque
from datetime import datetime, timedelta
import time
import docker
import requests

count=0
last_count=0
container_no=1
client = docker.from_env()


class SlidingWindowRequestCounter:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.request_timestamps = deque()
        self.count = 0

    def record_request(self, count, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()

        # Increment the count by the specified value
        self.count += count

        # Add the request timestamp
        self.request_timestamps.append((timestamp, count))

        # Remove timestamps older than the window size
        while self.request_timestamps and self.request_timestamps[0][0] < timestamp - timedelta(seconds=self.window_size):
            _, expired_count = self.request_timestamps.popleft()
            self.count -= expired_count

    def get_request_count(self):
        return self.count

request_counter = SlidingWindowRequestCounter()


def add_ip_to_file(ip_address, filename="backendips.txt"):
    # Open the file in append mode and write the IP address
    with open(filename, 'a') as file:
        file.write('\n'+ip_address)

def get_ips(filename="backendips.txt"):
    with open(filename, 'r') as file:
        lines = file.readlines()

    # Remove leading and trailing blank lines
    start = next((i for i, line in enumerate(lines) if line.strip()), None)
    end = next((i for i in range(len(lines)-1, -1, -1) if lines[i].strip()), None)

    ips = [line.strip() for line in lines[start:end+1]]
    return ips

def remove_ip_from_file(ip,filename="backendips.txt"):
    # Read the contents of the file
    with open(filename, 'r') as file:
        lines = file.readlines()

    # Remove the specified IP address from the list of lines
    lines = [line.strip() for line in lines if line.strip() != ip]

    # Rewrite the modified contents back to the file
    with open(filename, 'w') as file:
        file.write('\n'.join(lines))

def add_rules(ips):
    try:
        command = f"iptables -t nat -F PREROUTING"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)
        command = f"iptables -t nat -F POSTROUTING"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)

    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"
    

    iplen = len(ips)
    for i,ip in enumerate(ips):
        try:
            command = f"iptables -t nat -I PREROUTING -p tcp --dport 8080 -m statistic --mode nth --every {i+1} --packet 0 -j DNAT --to-destination {ip}:5000"
            result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)
            command = f"iptables -t nat -A POSTROUTING -p tcp -d {ip} --dport 5000 -j MASQUERADE"
            result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)

        except subprocess.CalledProcessError as e:
            print("here")
            return f"Error executing command: {e.stderr}"

def get_request_count(ip_address):
    try:
        command = f"iptables -t nat -L POSTROUTING -v | grep '{ip_address}' |" + "awk '{print $1}'"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)
        if not result:
            result=0
        return result
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"

def add_rule(ip):
    try:
        command = f"iptables -t nat -I PREROUTING -p tcp --dport 8080 -m statistic --mode nth --every {container_no} --packet 0 -j DNAT --to-destination {ip}:5000"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)
        command = f"iptables -t nat -A POSTROUTING -p tcp -d {ip} --dport 5000 -j MASQUERADE"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)
    except:
        pass

def remove_ip_rule(ip):
    try:
        command = f"iptables -t nat -D PREROUTING -p tcp --dport 8080 -m statistic --mode nth --every {container_no} --packet 0 -j DNAT --to-destination {ip}:5000"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)
        command = f"iptables -t nat -D POSTROUTING -p tcp -d {ip} --dport 5000 -j MASQUERADE"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)
    except:
        pass

def remove_container():
    container = client.containers.get(f"app{container_no}")
    ip = container.attrs['NetworkSettings']['IPAddress']
    container.stop()
    container.remove()
    remove_ip_rule(ip)
    remove_ip_from_file(ip)
    container_no-=1

def init_balancer():
    try:
        command = f"iptables -t nat -F PREROUTING"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)
        command = f"iptables -t nat -F POSTROUTING"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True)

    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"
    with open("backendips.txt", 'w') as file:
        pass
    global container_no
    ip_new=requests.get(f"http://172.17.0.1:5001/?conatiner_no={container_no}&scale=up").text
    add_rule(ip_new)
    add_ip_to_file(ip_new)
    container_no+=1
    

if __name__ == "__main__":
    threshold=5
    init_balancer()
    ips=get_ips()
    # print(ips)
    # add_rules(ips)
    # print(ips)
    no_of_req_ser=1 
    container_no=len(ips)+1
    while True:
        time.sleep(2)
        ips=get_ips()
        count=int(get_request_count(ips[0]))
        request_counter.record_request(count-last_count)
        total_in_window=request_counter.get_request_count()
        last_count=count
        
        no_of_ser=len(ips)
        no_of_req_ser = int(int(total_in_window)/threshold) + 1
        if no_of_req_ser == 0:
            no_of_req_ser=1 
        print("total",total_in_window,"req",no_of_req_ser,"ser",no_of_ser)
        if no_of_req_ser > no_of_ser:
            ip_new=requests.get(f"http://172.17.0.1:5001/?conatiner_no={container_no}&scale=up").text
            add_rule(ip_new)
            add_ip_to_file(ip_new)
            container_no+=1
        elif no_of_req_ser < no_of_ser:
            container_no-=1
            ip_new=requests.get(f"http://172.17.0.1:5001/?conatiner_no={container_no}&scale=down").text
            remove_ip_rule(ip_new)
            remove_ip_from_file(ip_new)


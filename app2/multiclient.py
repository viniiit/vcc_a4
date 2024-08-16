import requests
import threading
import time
from collections import defaultdict
import plotly.graph_objs as go

reqs = [50, 100, 150, 200]
# reqs = [5, 10]

class SendRequestThread(threading.Thread):
    def __init__(self, req_count):
        super().__init__()
        self.req_count = req_count
        self.start_time = None
        self.end_time = None

    def run(self):
        for _ in range(self.req_count):
            response = requests.get("http://localhost:8080/")
            print(response.text)

threads = []
times = []

for req in reqs:
    print(f"req {req}")
    start_time = time.time()
    i=1
    for _ in range(req):
        time.sleep(1)
        send_req_thread = SendRequestThread(1)
        send_req_thread.start()
        threads.append(send_req_thread)

    for thread in threads:
        thread.join()
    
    threads.clear()
    end_time = time.time()

    times.append(end_time - start_time)
    

print("All threads have finished. Proceeding with further actions...")

# Plotting the graph
data = [go.Scatter(x=reqs, y=[t for t in times], mode='lines+markers')]
layout = go.Layout(
    title='Request Count vs Time',
    xaxis=dict(title='Request Count'),
    yaxis=dict(title='Time (s)'),
)
fig = go.Figure(data=data, layout=layout)
fig.write_image('request_time_plot_least_con.png')

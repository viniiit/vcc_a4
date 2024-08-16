import requests
import time
# Make 10 requests
for _ in range(10):
    response = requests.get("http://localhost:8080/")
    print(response.text)
    time.sleep(1)
time.sleep(2)
response=requests.get("http://localhost:8080/")
print(response.text)

# app1/app1.py
from flask import Flask
import time

app1 = Flask(__name__)

@app1.route('/')
def hello_world():
    return 'Hello from App!'

if __name__ == '__main__':
    app1.run(debug=True, host='0.0.0.0')

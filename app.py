from flask import Flask, jsonify
import os
import socket
import time
import psutil

app = Flask(__name__)

# Get pod hostname
def get_pod_name():
    return os.environ.get('HOSTNAME', socket.gethostname())

@app.route('/')
def hello_world():
    return jsonify({
        'message': 'Hello World!',
        'service': 'Simple Flask API',
        'version': '1.0.0',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'pod': get_pod_name()
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'pod': get_pod_name()
    })

@app.route('/api/hello')
def api_hello():
    return jsonify({
        'message': 'Hello from the Flask API!',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'pod': get_pod_name()
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'running',
        'uptime': time.time() - psutil.boot_time(),
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent
        },
        'pod': get_pod_name(),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

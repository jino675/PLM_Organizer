from flask import Flask, request, jsonify
from app.context import ContextManager
import logging

# Disable default flask logging to avoid clutter
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
context_manager = ContextManager()

@app.route('/update_context', methods=['POST'])
def update_context():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
    # Expected keys: defect_id, plm_id, title
    context_manager.update_context(data)
    return jsonify({"status": "ok", "received": data})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "running"})

def start_server(port=5555):
    try:
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server Error: {e}")

from flask import Flask, request, jsonify
from app.context import ContextManager
import logging

# Disable all flask/werkzeug logging to avoid clutter and popup windows
import os
os.environ["WERKZEUG_RUN_MAIN"] = "true"  # Silence the "Debug mode" banner
logging.getLogger('werkzeug').disabled = True

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

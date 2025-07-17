# backend/app.py - Python Flask Backend with Embedded PyQt5 GUI

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import time
import random
import sys
import threading
import webbrowser # To open the browser if the app is not frozen

# PyQt5 imports for the GUI
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QThread, pyqtSignal

# --- Flask App Setup ---
# Configure Flask to serve static files from the 'static' directory
# and templates (if you had any, though not strictly needed for a single HTML file)
# The static_url_path='' makes it serve from the root, e.g., /index.html
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app) # Allow CORS for the embedded web engine

# --- In-memory Data Store (for simulation purposes only) ---
# In a real app, this would interact with Active Directory DNS
dns_data = {
    "example.com": [
        {"hostname": "www", "record_type": "A", "value": "192.168.1.100"},
        {"hostname": "api", "record_type": "CNAME", "value": "www.example.com"},
        {"hostname": "mail", "record_type": "MX", "value": "mail.example.com"},
        {"hostname": "txttest", "record_type": "TXT", "value": "v=spf1 include:_spf.google.com ~all"},
        {"hostname": "srvtest", "record_type": "SRV", "value": "0 5 5060 sip.example.com"},
    ],
    "sub.example.com": [
        {"hostname": "dev", "record_type": "A", "value": "192.168.1.101"},
        {"hostname": "test", "record_type": "A", "value": "192.168.1.102"},
    ],
    "anotherdomain.local": [
        {"hostname": "ftp", "record_type": "CNAME", "value": "dev.example.com"},
        {"hostname": "printer", "record_type": "A", "value": "192.168.1.103"},
        {"hostname": "vpn", "record_type": "A", "value": "192.168.1.104"},
    ]
}

audit_log = [] # In-memory audit log for demonstration

def log_action(level, message, user="Backend"):
    """Adds an entry to the audit log."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level.upper()} - User: {user} - {message}"
    audit_log.append(log_entry)
    print(log_entry) # Also print to console for debugging

# --- Flask API Endpoints ---

@app.route('/')
def serve_index():
    """Serves the main index.html file."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/connect', methods=['POST'])
def connect():
    """
    Simulates connection and zone discovery.
    In a real app, this would involve authenticating with AD
    and then querying DNS zones.
    """
    data = request.json
    dns_server = data.get('dnsServer')
    dc_ldap = data.get('dcLdap')
    username = data.get('username')
    password = data.get('password')

    log_action("INFO", f"Attempting connection to {dns_server} with user {username}", user=username)

    # Simulate delay and success/failure
    time.sleep(2)
    if username == "admin@example.com" and password == "password": # Simple dummy check
        log_action("INFO", "Connection and authentication successful (simulated).", user=username)
        return jsonify({"zones": list(dns_data.keys())}), 200
    else:
        log_action("ERROR", "Connection failed: Invalid credentials (simulated).", user=username)
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/records/<zone_name>', methods=['GET'])
def get_records(zone_name):
    """
    Fetches DNS records for a given zone.
    In a real app, this would query the AD DNS server.
    Supports optional record_type and search_term filters.
    """
    record_type_filter = request.args.get('record_type', 'All')
    search_term = request.args.get('search_term', '').lower()

    if zone_name not in dns_data:
        log_action("WARNING", f"Attempted to fetch records for non-existent zone: {zone_name}")
        return jsonify({"error": "Zone not found"}), 404

    records = dns_data[zone_name]
    filtered_records = []

    for record in records:
        match_type = (record_type_filter == 'All' or record['record_type'] == record_type_filter)
        match_search = (not search_term or
                        search_term in record['hostname'].lower() or
                        search_term in record['value'].lower())

        if match_type and match_search:
            filtered_records.append(record)

    log_action("INFO", f"Fetched {len(filtered_records)} records for zone {zone_name} (filtered).")
    return jsonify({"records": filtered_records}), 200

@app.route('/api/records/<zone_name>', methods=['POST'])
def add_record(zone_name):
    """
    Adds a new DNS record to a zone.
    In a real app, this would execute a command on the AD DNS server.
    """
    data = request.json
    hostname = data.get('hostname')
    record_type = data.get('record_type')
    value = data.get('value')

    if not all([hostname, record_type, value]):
        return jsonify({"error": "Missing data for new record"}), 400
    if zone_name not in dns_data:
        return jsonify({"error": "Zone not found"}), 404

    # Simulate success and add to in-memory data
    time.sleep(1)
    new_record = {"hostname": hostname, "record_type": record_type, "value": value}
    dns_data[zone_name].append(new_record)
    log_action("INFO", f"Added record (simulated): {hostname} {record_type} {value} in {zone_name}")
    return jsonify({"message": "Record added successfully (simulated)", "record": new_record}), 201

@app.route('/api/records/<zone_name>', methods=['PUT'])
def update_record(zone_name):
    """
    Updates an existing DNS record in a zone.
    In a real app, this would execute a command on the AD DNS server.
    """
    data = request.json
    hostname = data.get('hostname')
    record_type = data.get('record_type')
    old_value = data.get('old_value')
    new_value = data.get('new_value')

    if not all([hostname, record_type, old_value, new_value]):
        return jsonify({"error": "Missing data for record update"}), 400
    if zone_name not in dns_data:
        return jsonify({"error": "Zone not found"}), 404

    # Simulate success and update in-memory data
    time.sleep(1)
    found = False
    for record in dns_data[zone_name]:
        if record['hostname'] == hostname and record['record_type'] == record_type and record['value'] == old_value:
            record['value'] = new_value
            found = True
            break
    if found:
        log_action("INFO", f"Updated record (simulated): {hostname} {record_type} {old_value} -> {new_value} in {zone_name}")
        return jsonify({"message": "Record updated successfully (simulated)"}), 200
    else:
        log_action("ERROR", f"Record not found for update (simulated): {hostname} {record_type} {old_value} in {zone_name}")
        return jsonify({"error": "Record not found for update"}), 404

@app.route('/api/records/<zone_name>', methods=['DELETE'])
def delete_records(zone_name):
    """
    Deletes one or more DNS records from a zone.
    In a real app, this would execute commands on the AD DNS server.
    """
    data = request.json
    records_to_delete = data.get('records', [])

    if not records_to_delete:
        return jsonify({"error": "No records provided for deletion"}), 400
    if zone_name not in dns_data:
        return jsonify({"error": "Zone not found"}), 404

    deleted_count = 0
    failed_deletions = []
    initial_records_in_zone = list(dns_data[zone_name]) # Take a copy to iterate

    for rec_data in records_to_delete:
        hostname = rec_data.get('hostname')
        record_type = rec_data.get('record_type')
        value = rec_data.get('value')

        # Simulate deletion and update in-memory data
        time.sleep(0.5) # Simulate per-record delay
        original_len = len(dns_data[zone_name])
        dns_data[zone_name] = [
            r for r in dns_data[zone_name]
            if not (r['hostname'] == hostname and r['record_type'] == record_type and r['value'] == value)
        ]
        if len(dns_data[zone_name]) < original_len:
            deleted_count += 1
            log_action("INFO", f"Deleted record (simulated): {hostname} {record_type} {value} in {zone_name}")
        else:
            failed_deletions.append({"record": rec_data, "error": "Record not found or failed to delete (simulated)"})
            log_action("ERROR", f"Failed to delete record (simulated): {hostname} {record_type} {value} in {zone_name}")

    if failed_deletions:
        return jsonify({"message": f"Deleted {deleted_count} records, but some failed.", "failed_deletions": failed_deletions}), 202
    else:
        return jsonify({"message": f"Successfully deleted {deleted_count} records (simulated)"}), 200

@app.route('/api/bulk_update/<zone_name>', methods=['POST'])
def bulk_update(zone_name):
    """
    Applies bulk DNS changes (add/update).
    In a real app, this would iterate through changes and execute commands.
    """
    changes = request.json.get('changes', [])

    if not changes:
        return jsonify({"error": "No changes provided for bulk update"}), 400
    if zone_name not in dns_data:
        return jsonify({"error": "Zone not found"}), 404

    success_count = 0
    failed_changes = []

    for change in changes:
        hostname = change.get('hostname')
        record_type = change.get('record_type')
        new_value = change.get('new_value')
        old_value = change.get('old_value') # old_value will be null for new records

        if not all([hostname, record_type, new_value]):
            failed_changes.append({"change": change, "error": "Missing data"})
            continue

        # Simulate success/failure for each change
        time.sleep(0.2) # Simulate small delay per change
        if random.random() > 0.1: # 90% success rate
            if old_value:
                # Simulate update in-memory
                found = False
                for record in dns_data[zone_name]:
                    if record['hostname'] == hostname and record['record_type'] == record_type and record['value'] == old_value:
                        record['value'] = new_value
                        found = True
                        break
                if found:
                    success_count += 1
                    log_action("INFO", f"Bulk updated record (simulated): {hostname} {record_type} {old_value} -> {new_value} in {zone_name}")
                else:
                    failed_changes.append({"change": change, "error": "Record not found for update (simulated)"})
                    log_action("ERROR", f"Bulk update failed (record not found): {hostname} {record_type} {old_value} -> {new_value} in {zone_name}")
            else:
                # Simulate add in-memory
                dns_data[zone_name].append({"hostname": hostname, "record_type": record_type, "value": new_value})
                success_count += 1
                log_action("INFO", f"Bulk added record (simulated): {hostname} {record_type} {new_value} in {zone_name}")
        else:
            failed_changes.append({"change": change, "error": "Simulated failure"})
            log_action("ERROR", f"Bulk update failed (simulated): {hostname} {record_type} in {zone_name}")

    if failed_changes:
        return jsonify({"message": f"Completed bulk update. {success_count} succeeded, {len(failed_changes)} failed.", "failed_changes": failed_changes}), 200
    else:
        return jsonify({"message": f"All {success_count} bulk changes applied successfully (simulated)"}), 200

@app.route('/api/audit_logs', methods=['GET'])
def get_audit_logs():
    """Returns the in-memory audit log."""
    log_action("INFO", "Audit logs requested.")
    return jsonify({"logs": audit_log}), 200

# --- Flask Server Thread ---
class FlaskThread(QThread):
    """Thread to run the Flask development server."""
    def run(self):
        # Use a specific port, e.g., 5000, for the frontend to connect to.
        # debug=False for production build to avoid reloader issues with PyInstaller.
        app.run(port=5000, debug=False, use_reloader=False)

# --- PyQt5 GUI Setup ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portable DNS Manager")
        self.setGeometry(100, 100, 1200, 800) # Initial window size

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.browser = QWebEngineView()
        layout.addWidget(self.browser)

        # Determine the path to index.html when running from PyInstaller or locally
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller executable
            # sys._MEIPASS is the path to the temporary folder where PyInstaller extracts bundled files.
            html_path = os.path.join(sys._MEIPASS, 'static', 'index.html')
        else:
            # Running in development mode (e.g., from PyCharm)
            # Assumes app.py is in 'backend' and index.html is in 'backend/static'
            current_dir = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(current_dir, 'static', 'index.html')

        # Load the local HTML file
        self.browser.setUrl(QUrl.fromLocalFile(html_path))

        # Optional: Connect to a signal for when the page is loaded (useful for debugging)
        self.browser.loadFinished.connect(self.on_load_finished)

    def on_load_finished(self, ok):
        if ok:
            log_action("INFO", "Frontend GUI loaded successfully in QWebEngineView.")
        else:
            log_action("ERROR", "Failed to load frontend GUI in QWebEngineView.", user="GUI")

# --- Main Application Entry Point ---
if __name__ == '__main__':
    # 1. Start Flask server in a separate thread
    flask_thread = FlaskThread()
    flask_thread.start()
    log_action("INFO", "Flask server thread started.")

    # Give Flask a moment to start up before the GUI tries to connect
    time.sleep(1)

    # 2. Start PyQt GUI
    app_gui = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    # Handle application exit: stop Flask thread gracefully (optional, but good practice)
    app_gui.aboutToQuit.connect(flask_thread.quit) # Signal Flask thread to quit
    app_gui.aboutToQuit.connect(flask_thread.wait) # Wait for Flask thread to finish

    sys.exit(app_gui.exec_())

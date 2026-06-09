"""
run.py - One command to start the XML to SQL Agent and open the browser.
Usage:  python run.py
"""
import subprocess
import webbrowser
import time
import sys
import os

PORT = 8000
URL  = f"http://localhost:{PORT}"

print("=" * 50)
print("   XML to BigQuery SQL Converter Agent")
print("=" * 50)
print(f"\nStarting server on {URL} ...\n")

# Start streamlit as a subprocess
server = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
     "--server.port", str(PORT), "--server.headless", "true"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

# Wait a moment for the server to boot
time.sleep(4)

# Open the browser automatically
print(f"Opening browser at {URL} ...\n")
webbrowser.open(URL)

print("Agent is running! Press Ctrl+C to stop.\n")

try:
    server.wait()
except KeyboardInterrupt:
    print("\nShutting down server...")
    server.terminate()
    server.wait()
    print("Server stopped.")

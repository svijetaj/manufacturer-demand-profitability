"""
Native Desktop Application Launcher using PyWebView.
Wraps the Finance & Demand Intelligence Platform in a true native OS desktop window.
"""

import os
import sys
import time
import socket
import subprocess
import webview

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_SCRIPT = os.path.join(BASE_DIR, "app.py")
PORT = 8501

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_server():
    """Starts the Streamlit background process in headless mode."""
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_PORT"] = str(PORT)
    env["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    env["STREAMLIT_THEME_BASE"] = "dark"

    python_bin = sys.executable

    # Launch headless server process
    proc = subprocess.Popen(
        [python_bin, "-m", "streamlit", "run", APP_SCRIPT, 
         "--server.headless=true", 
         f"--server.port={PORT}", 
         "--server.address=127.0.0.1",
         "--browser.gatherUsageStats=false",
         "--theme.base=dark"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return proc

def main():
    server_process = None
    if not is_port_open(PORT):
        print("Starting local analytics engine...")
        server_process = start_server()
        
        # Wait up to 10 seconds for the server to be ready
        retries = 20
        while retries > 0 and not is_port_open(PORT):
            time.sleep(0.5)
            retries -= 1

    print("Launching Native Desktop Window...")
    
    # Create the native desktop window
    window = webview.create_window(
        title="Enterprise Demand & Profit Intelligence Platform",
        url=f"http://127.0.0.1:{PORT}",
        width=1350,
        height=880,
        min_size=(1000, 680),
        background_color="#0b0f19",
        text_select=True
    )
    
    # Start the desktop window (blocks until closed)
    webview.start()

    # Clean up server on window close
    if server_process:
        print("Closing application...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()

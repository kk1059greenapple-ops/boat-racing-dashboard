import subprocess
import time
import re
import sys
import os

print("Starting Cloudflared tunnel for port 8000...")
try:
    # Try fetching cloudflared if not installed locally via npx, but we don't have npx.
    # We will use the python module we just installed: flask-cloudflared includes a binary download.
    from flask_cloudflared import _run_cloudflared
    
    port = 8000
    command = _run_cloudflared(port)
    
    print(f"Cloudflared running. Press Ctrl+C to stop.")
    
    # We just want to get the URL. Flask-cloudflared runs it in a subprocess and patches stdout.
    # Let's just run it manually to extract the URL.
    
except Exception as e:
    print(f"Error: {e}")


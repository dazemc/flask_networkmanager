import os

cwd = os.getcwd()
service = f"""
[Unit]
Description=Wipi Portal
After=network.target
[Service]
WorkingDirectory={cwd}
ExecStart={cwd}/startup.sh
[Install]
WantedBy=default.target
"""

with open(f"{cwd}/wipi.service", "w", encoding="utf-8") as s_file:
    s_file.write(service)

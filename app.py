import subprocess
import json
import time
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DEBUG_HOTSPOT = False
HOTSPOT_IP = "192.168.6.9"

valid_queries = ["show_connections", "show_credentials", "delete_credentials"]
connection_values = [
    "id=",
    "uuid=",
    "type=",
    "autoconnect=",
    "interface-name=",
    "timestamp=",
    "mode=",
    "ssid=",
    "group=",
    "key-mgmt=",
    "pairwise=",
    "proto=",
    "psk=",
    "method=",
    "addr-gen-mode=",
    "method=",
]


@app.route("/rec_creds", methods=["GET"])
def handle_queries() -> str | dict:
    if request.method == "GET":
        query = request.query_string.decode("utf-8")
        find_query = query.find("=")
        if find_query != -1:
            query = query[:find_query]
        if query in valid_queries:
            if query == "show_connections":
                return show_connections()
            if query == "show_credentials":
                return show_credentials(request.args["show_credentials"])
            if query == "delete_credentials":
                return delete_credentials(request.args["delete_credentials"])
        return f"QUERY: {query}\nNot a valid query."
    return "Not a GET method"


@app.route("/send_creds", methods=["POST"])
def save_credentials() -> str:
    if request.method == "POST":
        r = json.loads(request.data)
        time.sleep(3)
        if connect_wifi(r["SSID"], r["PASS"]):
            if DEBUG_HOTSPOT:
                enable_hotspot()
            # will not be able to return because wifi connection gets lost, will send it with credentials instead
            # return {"local_ip": get_local_ip()}
            return "Connected"
        return "Error connecting"
    return "Not a POST method"


def show_connections() -> dict:
    return {"saved_connections": get_connections()}


def get_connections() -> list:
    show_wifi = subprocess.check_output(
        ["ls", "/etc/NetworkManager/system-connections/"]
    )
    conns = show_wifi.decode("utf-8").splitlines()
    print(conns)
    return [v.replace(".nmconnection", "") for v in conns]


def get_credentials(ssid) -> dict | str:
    saved_connections = get_connections()
    if ssid in saved_connections:
        credentials = str(
            subprocess.check_output(
                ["cat", f"/etc/NetworkManager/system-connections/{ssid}.nmconnection"]
            )
        )
        creds_parsed = {}
        for v in connection_values:
            creds_parsed[v[:-1]] = parse_credentials(credentials, v)[1]
        if ssid == "Hotspot":
            creds_parsed["local-ip"] = HOTSPOT_IP
        creds_parsed["local-ip"] = get_local_ip()
        return creds_parsed
    return f"SSID: {ssid}\nNot in saved connections."


def show_credentials(ssid) -> dict:
    return {request.args["show_credentials"]: get_credentials(ssid)}


def delete_credentials(ssid) -> str:
    subprocess.run(
        [
            "nmcli",
            "connection",
            "delete",
            ssid,
        ],
        check=False,
    )
    return f"Deleted {ssid}"


def parse_credentials(credentials, ingest) -> list:
    start = credentials.find(ingest)
    section = credentials[start:]
    end = section.find("\\")
    value = section[:end]
    split = value.split("=")
    if start == -1:
        return [ingest[:-1], ""]
    return split


def enable_hotspot() -> None:
    cycle_networking()
    subprocess.run(
        [
            "nmcli",
            "c",
            "up",
            "Hotspot",
        ],
        check=False,
    )


def cycle_networking() -> None:
    subprocess.run(["nmcli", "r", "wifi", "off"], check=False)
    subprocess.run(["nmcli", "r", "wifi", "on"], check=False)
    time.sleep(1)


def connect_wifi(ssid, password) -> bool:
    cycle_networking()
    check_wifi = subprocess.check_output(
        ["nmcli", "device", "wifi", "connect", ssid, "password", password]
    )
    if "successfully" in check_wifi.decode("utf-8"):
        return True
    return False


def get_local_ip() -> str:
    addr = subprocess.check_output(
        [
            "sh",
            "./scripts/get_ip.sh"
        ]
    )
    return addr.decode("utf-8")

if __name__ == "__main__":
    enable_hotspot()
    app.run(debug=True, host="0.0.0.0", port=80)

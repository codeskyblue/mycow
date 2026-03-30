import os
import base64
import json
import subprocess
import requests
import argparse
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

os.environ["PATH"] += ":./sing-box-1.14.0-alpha.7-linux-amd64/"

CONFIG_FILE = "./config.json"
TEMPLATE_FILE = "./config.json.tmpl"


def get_subscription_url():
    sub_url = None

    if os.path.exists(".env"):
        load_dotenv()

    sub_url = os.getenv("SUB_URL")

    return sub_url


def decode_base64(data):
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return base64.b64decode(data)


def fetch_subscription(sub_url):
    response = requests.get(sub_url, timeout=20)
    data = response.content

    try:
        decoded = decode_base64(data).decode()
    except Exception:
        decoded = data.decode()

    return decoded.strip().splitlines()


def parse_vmess(link):
    raw = decode_base64(link[8:]).decode()
    j = json.loads(raw)

    outbound = {
        "type": "vmess",
        "tag": j.get("ps", j["add"]),
        "server": j["add"],
        "server_port": int(j["port"]),
        "uuid": j["id"],
        "security": "auto"
    }

    if j.get("net") == "ws":
        outbound["transport"] = {
            "type": "ws",
            "path": j.get("path", "/"),
            "headers": {
                "Host": j.get("host", "")
            }
        }

    return outbound


def parse_vless(link):
    u = urlparse(link)

    query = parse_qs(u.query)

    outbound = {
        "type": "vless",
        "tag": u.hostname,
        "server": u.hostname,
        "server_port": u.port,
        "uuid": u.username
    }

    if "type" in query and query["type"][0] == "ws":
        outbound["transport"] = {
            "type": "ws",
            "path": query.get("path", ["/"])[0]
        }

    return outbound


def parse_ss(link):
    payload = link[5:]

    if "#" in payload:
        payload = payload.split("#")[0]

    decoded = decode_base64(payload).decode()

    method_pass, server = decoded.split("@")
    method, password = method_pass.split(":")
    host, port = server.split(":")

    return {
        "type": "shadowsocks",
        "tag": host,
        "server": host,
        "server_port": int(port),
        "method": method,
        "password": password
    }


def parse_trojan(link):
    u = urlparse(link)

    return {
        "type": "trojan",
        "tag": u.hostname,
        "server": u.hostname,
        "server_port": u.port,
        "password": u.username
    }


def parse_nodes(lines):
    nodes = []

    for line in lines:
        try:
            if line.startswith("vmess://"):
                nodes.append(parse_vmess(line))

            elif line.startswith("vless://"):
                nodes.append(parse_vless(line))

            elif line.startswith("ss://"):
                nodes.append(parse_ss(line))

            elif line.startswith("trojan://"):
                nodes.append(parse_trojan(line))

        except Exception as e:
            print("skip node:", e)

    return nodes


def update_config(nodes):
    with open(TEMPLATE_FILE) as f:
        config = json.load(f)

    tags = []

    for i, node in enumerate(nodes):
        tag = f"node-{i}"
        node["tag"] = tag
        tags.append(tag)

    config["outbounds"] = nodes + [
        {
            "type": "urltest",
            "tag": "proxy",
            "outbounds": tags,
            "url": "http://www.gstatic.com/generate_204",
            "interval": "5m"
        },
        {
            "type": "direct",
            "tag": "direct"
        }
    ]

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def reload_singbox():
    subprocess.run(
        ["sing-box", "check", "-c", CONFIG_FILE],
        check=True
    )

    subprocess.run(["pkill", "-HUP", "sing-box"])


def main():
    parser = argparse.ArgumentParser(description="Update sing-box config from subscription")
    parser.add_argument("--sub-url", help="Subscription URL (overrides env and .env)")
    args = parser.parse_args()

    sub_url = args.sub_url or get_subscription_url()

    if not sub_url:
        print("Error: Subscription URL not provided")
        print("Please provide it via:")
        print("  1. Command line argument: --sub-url <url>")
        print("  2. Environment variable: SUB_URL")
        print("  3. .env file: SUB_URL=<url>")
        return

    print("downloading subscription...")

    lines = fetch_subscription(sub_url)

    nodes = parse_nodes(lines)

    print("parsed nodes:", len(nodes))

    if not nodes:
        print("no nodes parsed")
        return

    update_config(nodes)

    reload_singbox()

    print("sing-box reloaded successfully")


if __name__ == "__main__":
    main()

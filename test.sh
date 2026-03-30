#!/bin/bash

export PATH="$PATH:./sing-box-1.14.0-alpha.7-linux-amd64/"

echo "=== Checking config file ==="
if [ ! -f ./config.json ]; then
    echo "config.json not found, run update_singbox.py first"
    exit 1
fi
echo "config.json exists"

echo ""
echo "=== Validating config ==="
sing-box check -c ./config.json
if [ $? -ne 0 ]; then
    echo "Config validation failed"
    exit 1
fi
echo "Config validation passed"

echo ""
echo "=== Testing proxy connectivity ==="
if curl -x socks5://127.0.0.1:10808 -s -o /dev/null -w "HTTP %{http_code} - %{time_total}s" --connect-timeout 10 http://www.google.com/generate_204; then
    echo ""
    echo "Proxy is working"
else
    echo ""
    echo "Proxy test failed, make sure sing-box is running (./start.sh)"
    exit 1
fi

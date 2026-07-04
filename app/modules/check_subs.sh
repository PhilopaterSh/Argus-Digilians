#!/usr/bin/env bash
echo "[*] Starting manual subdomain verification..."
subfinder -d vulnweb.com -silent | head -n 30 > /tmp/subs.txt
while read s; do
    res=$(curl -o /dev/null -s -L -w "%{http_code}" --connect-timeout 3 "http://$s")
    echo "$s: $res"
done < /tmp/subs.txt

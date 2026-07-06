#!/bin/bash
# Argus Recon Engine - Robust Version
DOMAIN=$1
[ -z "$DOMAIN" ] && echo "Usage: argus_recon <domain>" && exit 1

# Setup Paths
export PATH=$PATH:/home/kali/go/bin:/home/kali/.pdtm/go/bin
RAW_FILE="/tmp/argus_raw_$DOMAIN.txt"
ALIVE_FILE="/tmp/argus_alive_$DOMAIN.txt"

rm -f $RAW_FILE $ALIVE_FILE

echo "[INFO] Phase 1: OSINT Discovery..."
subfinder -d $DOMAIN -silent >> $RAW_FILE
assetfinder --subs-only $DOMAIN >> $RAW_FILE
findomain -t $DOMAIN -q >> $RAW_FILE

echo "[INFO] Phase 2: Brute-Force..."
WORDLIST="/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt"
[ ! -f "$WORDLIST" ] && echo "www" > /tmp/mini.txt && WORDLIST="/tmp/mini.txt"
gobuster dns --domain $DOMAIN -w $WORDLIST --quiet | grep "Found:" | awk '{print $2}' >> $RAW_FILE

echo "[INFO] Phase 3: Validation..."
sort -u $RAW_FILE -o $RAW_FILE

# Use ProjectDiscovery httpx if possible
HTTPX="/home/kali/.pdtm/go/bin/httpx"
[ ! -x "$HTTPX" ] && HTTPX=$(which httpx)

if [ -f "$RAW_FILE" ] && [ -s "$RAW_FILE" ]; then
    cat $RAW_FILE | $HTTPX -silent -threads 50 > $ALIVE_FILE
fi

echo "--- 🛡️ MAXIMIZED SUBDOMAIN DISCOVERY: $DOMAIN ---"
echo "[INFO] Total potential: $(wc -l < $RAW_FILE 2>/dev/null || echo "0")"
echo "[INFO] Total verified alive: $(wc -l < $ALIVE_FILE 2>/dev/null || echo "0")"
echo ""
echo "[INFO] TOP VERIFIED SUBDOMAINS:"
cat $ALIVE_FILE | head -n 50
echo ""
echo "[INFO] INFRASTRUCTURE POINTERS:"
cat $ALIVE_FILE | head -n 10 | while read sub; do
    clean_sub=$(echo "$sub" | sed -E 's|https?://||; s|/.*$||')
    cname=$(dig CNAME +short "$clean_sub" | head -n 1)
    [ -n "$cname" ] && echo "[CNAME] $sub -> $cname"
done

# DO NOT delete ALIVE_FILE so Argus can read it
rm -f $RAW_FILE 2>/dev/null

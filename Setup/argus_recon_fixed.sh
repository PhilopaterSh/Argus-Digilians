#!/bin/bash
# Argus Professional Recon Engine (Native Linux)
DOMAIN=$1
[ -z "$DOMAIN" ] && echo "Usage: argus_recon <domain>" && exit 1

RAW_FILE="/tmp/argus_raw_$DOMAIN.txt"
ALIVE_FILE="/tmp/argus_alive_$DOMAIN.txt"
WORDLIST="/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt"
[ ! -f "$WORDLIST" ] && echo "www" > /tmp/mini.txt && WORDLIST="/tmp/mini.txt"

echo "[*] Phase 1: Passive OSINT..."
subfinder -d $DOMAIN -silent > $RAW_FILE
assetfinder --subs-only $DOMAIN >> $RAW_FILE
findomain -t $DOMAIN -q >> $RAW_FILE
amass enum -passive -d $DOMAIN >> $RAW_FILE

echo "[*] Phase 2: Active Brute-Force..."
gobuster dns -d $DOMAIN -w $WORDLIST -z --quiet | grep "Found:" | awk "{print \$2}" >> $RAW_FILE

echo "[*] Phase 3: Permutations..."
sort -u $RAW_FILE -o $RAW_FILE
if command -v dnsgen &>/dev/null; then
    dnsgen $RAW_FILE >> $RAW_FILE
fi

echo "[*] Phase 4: Resolution & Validation (anew + httpx)..."
sort -u $RAW_FILE -o $RAW_FILE

# Use anew to keep only unique entries
cat $RAW_FILE | /usr/local/bin/anew /tmp/unique_$DOMAIN.txt > /dev/null

# Use httpx to find truly ALIVE web servers (the most critical part)
if [ -f "/usr/local/bin/httpx" ]; then
    cat /tmp/unique_$DOMAIN.txt | /usr/local/bin/httpx -silent -fc 404,500,502 -threads 50 > $ALIVE_FILE        
else
    # Fallback to puredns or host if httpx is missing
    if command -v puredns &>/dev/null; then
        puredns resolve /tmp/unique_$DOMAIN.txt --quiet > $ALIVE_FILE
    else
        cat /tmp/unique_$DOMAIN.txt | xargs -I{} host -W 2 {} | grep "has address" | awk "{print \$1}" > $ALIVE_FILE
    fi
fi

echo "[*] Phase 5: Deep DNS Analysis..."
ALIVE_COUNT=$(wc -l < $ALIVE_FILE)
echo "--- 🛡️ MAXIMIZED SUBDOMAIN DISCOVERY: $DOMAIN ---"
echo "[+] Total Potential: $(wc -l < $RAW_FILE)"
echo "[+] Total Verified Alive (Web): $ALIVE_COUNT"
rm /tmp/unique_$DOMAIN.txt 2>/dev/null
echo ""
echo "[*] TOP VERIFIED SUBDOMAINS:"
head -n 50 $ALIVE_FILE
echo ""
echo "[*] INFRASTRUCTURE POINTERS (CNAME/MX):"
head -n 10 $ALIVE_FILE | while read sub; do
    # Clean domain: remove http/https and trailing slash
    clean_sub=$(echo "$sub" | sed -E 's|https?://||; s|/.*$||')
    cname=$(dig CNAME +short +time=3 +tries=2 "$clean_sub")
    [ -n "$cname" ] && echo "[CNAME] $sub -> $cname"
    mx=$(dig MX +short +time=3 +tries=2 "$clean_sub")
    [ -n "$mx" ] && echo "[MX] $sub -> $mx"
done

rm $RAW_FILE $ALIVE_FILE 2>/dev/null

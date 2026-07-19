import re
import requests

def main():
    target = "http://testasp.vulnweb.com"
    print(f"[*] Crawling {target} for valid links...")
    try:
        r = requests.get(target, timeout=10)
        content = r.text
        # Find all hrefs
        links = re.findall(r'href=["\'](.*?)["\']', content)
        unique_links = sorted(list(set(links)))
        print(f"[+] Found {len(unique_links)} unique links:")
        for link in unique_links:
            if not link.startswith('#') and 'javascript' not in link:
                print(f"  - {link}")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()

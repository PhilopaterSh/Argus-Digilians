class CrawlerService:
    """Discovers internal links and entry points to expand the attack surface."""

    def __init__(self, runner, memory):
        self.runner = runner
        self.memory = memory

    def crawl_target(self, url):
        """Discovers internal links and entry points using curl and grep."""
        print(f"[*] [Argus-Core] Crawling target: {url}")
        cmd = f"curl -s -L {url} | grep -oE 'href=\"[^\"]+\"' | cut -d'\"' -f2 | sort -u"
        res = self.runner.run(cmd)
        
        links = [l for l in res.split('\n') if l.strip() and not l.startswith(('#', 'javascript'))]
        
        clean_target = url.replace("https://", "").replace("http://", "").split("/")[0]
        for link in links[:20]:
            self.memory.add_finding(clean_target, "crawler", "link", link, f"Discovered link: {link}")        

        return f"--- 🕸️ CRAWLER REPORT: {url} ---\nFound {len(links)} links. Top findings:\n" + "\n".join(links[:15])

from app.tools.utils import normalize_domain_for_memory, shell_quote


class CrawlerService:
    """Discovers internal links and entry points to expand the attack surface."""

    def __init__(self, runner, memory):
        """Store the shared command runner and memory service.

        Args:
            runner: Object with a `run(command)` method that executes a
                shell command (via WSL/SSH) and returns its output as a str.
            memory (ArgusMemory): Blackboard memory service used to persist
                discovered links.
        """
        self.runner = runner
        self.memory = memory

    def crawl_target(self, url):
        """Discovers internal links and entry points using curl and grep.

        Args:
            url (str): Target URL to crawl.

        Returns:
            str: A report of discovered links (up to 15 shown), or "Found 0
            links" if the target is unreachable/times out (--max-time
            bounds this to 15s so an unreachable target - live-confirmed
            against a real, currently-down practice site during specs/018
            CHK090's own verification - fails fast instead of blocking on
            command_runner.py's much longer generic default timeout).
        """
        print(f"[*] [Argus-Core] Crawling target: {url}")
        # Extract href= AND src=. href alone systematically misses the exact
        # endpoints traversal/LFI sinks live behind: PortSwigger's "File path
        # traversal, simple case" exposes its vulnerable `/image?filename=`
        # only in an <img src>, so an href-only crawl reported "Found 0 links"
        # and the traversal scanner had no attack surface to inherit.
        cmd = (
            f"curl -s -L --max-time 15 --connect-timeout 5 {shell_quote(url)} "
            f"| grep -oE '(href|src)=\"[^\"]+\"' | cut -d'\"' -f2 | sort -u"
        )
        res = self.runner.run(cmd)
        
        links = [l for l in res.split('\n') if l.strip() and not l.startswith(('#', 'javascript'))]
        
        clean_target = normalize_domain_for_memory(url)
        for link in links[:20]:
            self.memory.add_finding(clean_target, "crawler", "link", link, f"Discovered link: {link}")        

        return f"--- [WEB] CRAWLER REPORT: {url} ---\nFound {len(links)} links. Top findings:\n" + "\n".join(links[:15])

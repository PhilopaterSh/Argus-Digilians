# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do you use the Wayback Machine and robots.txt together to find forgotten, likely-vulnerable files?

## Analysis / Response

These two techniques complement each other and both come in during Step Two, after the main-app pass.

**robots.txt first.** Once subdomain scanning finishes, I quickly scan `/robots.txt` on each domain. robots.txt lists endpoints the owner does and does *not* want indexed, so if a subdomain runs some third-party software, robots.txt may reveal information about what's on it. I treat it as a great starting indicator of whether a subdomain is worth scanning further for directories and files — I personally like subdomains that have functionality to play with rather than relying on a wordlist. You can scan robots.txt quickly with Burp Intruder by setting the position, and even run a small local PHP redirect script under XAMPP to probe which domains are alive and follow redirects.

**Then expand with the Wayback Machine.** You can expand your robots.txt data by scraping results from `WayBackMachine.org`. It lets you view a site's history from years ago, and old files referenced in robots.txt years ago are sometimes still present today. Those forgotten files usually contain old code that is more than likely vulnerable. I've had high success pairing wide-scope programs with the Wayback Machine, and there are tools referenced early in the guide to automate the scraping.

**Why this works.** robots.txt points you at paths the owner deliberately excluded (often the interesting/legacy ones), and the Wayback Machine resurrects paths they've since removed from the live site but never actually deleted. Together they surface old, forgotten, under-tested code. Keep all of this within the program's scope.

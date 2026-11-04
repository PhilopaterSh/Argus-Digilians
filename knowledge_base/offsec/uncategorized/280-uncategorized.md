# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Do you take notes while hunting? How, and why does it matter?

## Analysis / Response

Yes - and it's one area where researchers go wrong because note-taking isn't discussed enough. I made the mistake of not writing anything down when I started. Writing notes as you hack actually saves you from burnout: when you feel like you've exhausted every feature, your notes let you revisit interesting endpoints with a fresh mindset and a new approach.

How: there's no right or wrong system. Personally I use Sublime Text and jot down interesting endpoints, behaviour, and parameters as I browse and test. When I hit a feature I can't exploit yet, I note what I tried and what I suspect it's vulnerable to, then come back later. Never burn yourself out - if your gut says you're tired of a feature, move on.

Notes also feed your wordlists. If on example.com you discover /admin, /admin-new, /server_health and params "debug" and "isTrue", save examplecom-endpoints.txt and params.txt. Then test those across multiple domains and build a global-endpoints.txt of commonly found endpoints. Over time you accumulate per-domain and global lists that let you map applications much faster - a treasure map of your target.

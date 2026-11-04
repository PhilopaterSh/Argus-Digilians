# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do you use Google dorking to find login and registration pages, and why target those?

## Analysis / Response

Login and register pages are prime targets because they change often (developers tweak them for user experience) and Google's robots index and remember a lot of that history. To surface them:

    site:example.com inurl:register inurl:&
    site:example.com inurl:signup inurl:&
    site:example.com inurl:join inurl:&

The inurl:& trick pulls up pages that carry parameters, which is exactly what you want - parameters are where redirect controls, null-byte handling, and injection live. Also dork more broadly for functional keywords (login, register, signup, profile, upload, api, developer, upgrade, passwordreset) to find functional subdomains and old indexed endpoints you missed on the live site.

Why target auth pages: they almost always use redirect parameters (returnUrl, goto, etc.), handle user-controlled input that gets reflected, and are rich in logic (null-byte email tricks, host-header reset-token leaks, social-login OAuth token leaks). Finding historical/variant auth endpoints via Google often reveals old, less-protected code. Authorized scope only.

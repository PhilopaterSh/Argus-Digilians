# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Walk me through Web Security for Developers — Don’t Be an Accessory: Protecting Against Server-Side Forgery with practical steps from the source material.

## Analysis / Response

Based on Web Security for Developers (Protecting Against Server-Side Forgery):

Protecting Against Server-Side Forgery
                   You can protect yourself against server-side forgery at several levels. The
                   first, and most important step, is to audit any parts of your code that make
                   outbound HTTP requests. You will almost always know ahead of time which
                   domains need to be invoked as part of API calls, so the construction of
                   URLs for API calls should use web domains recorded in your configuration
                   or code rather than coming from the client. One way of ensuring this is to
                   use the software development kit (SDK) that is usually made freely available
                   with most APIs.
                        Because you should be following the practice of defense in depth—pro-
                   tecting yourself from vulnerabilities in multiple, overlapping ways—it makes
                   sense to install safeguards against SSRF at the network level too. Whitelisting
                   the individual domains that you need access to in your firewall, and banning
                   all others, is a good way to catch any security issues you may have overlooked
                   during code review.

Use only on systems you are authorized to test; capture evidence and include remediation.

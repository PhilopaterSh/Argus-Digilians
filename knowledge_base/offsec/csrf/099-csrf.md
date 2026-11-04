# CSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: csrf
- cwe: CWE-352

## Scenario

What should a web pentester know about Web Security for Developers — Cross-Site Scripting Attacks: CSRF is a remarkably common vulnerability that most major websites?

## Analysis / Response

Based on Web Security for Developers (CSRF is a remarkably common vulnerability that most major websites):

CSRF is a remarkably common vulnerability that most major websites
have exhibited at one time or another. Attackers have used CSRF to steal

                    Gmail contact lists, trigger one-click purchases on Amazon, and change
                    router configuration. This chapter examines how CSRF attacks typically
                    work and shows some coding practices that protect against them.

     Anatomy of a CSRF Attack
                    Attackers usually launch CSRF attacks by exploiting websites that imple-
                    ment GET requests that change the state of a web server. A GET request is trig-
                    gered when a victim clicks a link, allowing the attacker to craft misleading
                    links into the target site that perform unexpected actions. GET requests are
                    the only type of HTTP request that contain the entirety of the request’s
                    contents in a URL, so they’re uniquely vulnerable to CSRF attacks.
                        In an early iteration of Twitter, you could create tweets via GET requests
                    rather than the POST requests the site currently uses. This oversight made
                    Twitter vulnerable to CSRF attacks: it made it possible to create URL links
                    that, when clicked, would post on a user’s timeline. Listing 8-1 shows one of
                    these URL links.

https://twitter.com/share/update?status=in%20ur%20twitter%20CSRF-ing%20ur%20tweets

Listing 8-1: A link that, at one point, would have tweeted the text in ur twitter CSRF-ing ur tweets to a victim’s
timeline when clicked

                        One canny hacker used this loophole to create a viral worm on Twitter.
                    Because they could use a single GET request to write a tweet, they constructed
                    a malicious link that, when clicked, would post a tweet containing an obscene
                    message and the same malicious link. When readers of the tweet clicked the
                    link that the first victim tweeted, they too were tricked into tweeting the
                    same thing.

Use only on systems you are authorized to test; capture evidence and include remediation.

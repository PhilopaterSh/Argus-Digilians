# RESOURCE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: resource
- cwe: CWE-400

## Scenario

Describe methodology and key techniques for Web Security for Developers — Denial-of-Service Attacks: The only person who should know whether a user has signed up to your during an authorized assessment.

## Analysis / Response

Based on Web Security for Developers (The only person who should know whether a user has signed up to your):

The only person who should know whether a user has signed up to your
site is the user themselves. Make sure login forms and password reset pages
do not permit a hacker to mine your site for a list of users: keep error and
information messages generic, whether a username exists or not.
Protect Your Cookies
If an attacker can steal your cookies, they can hijack your users’ identities.
Add the HttpOnly keyword to your Set-Cookie response headers so cookies
cannot be read by malicious JavaScript. Add the Secure keyword so that
cookies are sent only over HTTPS.
Protect Sensitive Resources (Even If You Don’t Link to Them)
Check that a user has permissions to access any sensitive resource on your
site before returning it in an HTTP request—even if that resource isn’t
listed in search pages or linked to from elsewhere.

Use only on systems you are authorized to test; capture evidence and include remediation.

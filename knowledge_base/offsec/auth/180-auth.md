# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Web Security for Developers — Compromising Authentication: Attackers may also use timing attacks to enumerate users by measuring

## Analysis / Response

Based on Web Security for Developers (Attackers may also use timing attacks to enumerate users by measuring):

Attackers may also use timing attacks to enumerate users by measuring
HTTP response times. Hashing a password is a time-consuming operation;
though it typically takes less than a second, it’s still a measurable amount
of time. If your site calculates password hashes only when a user enters a
valid username, an attacker can measure the slightly slower response time
to infer which accounts exist on the site. Make sure your site calculates pass-
word hashes during authentication even for invalid usernames.
     You should prevent your password-reset screen from revealing that a user-
name exists, too. If an attacker clicks a “Forgotten password” link and types
in an email address to request a password-reset link, the response message
on the page shouldn’t reveal whether a reset email was sent. This prevents the
attacker from knowing whether that email address is tied to an account on
your site. Keep the message neutral: something like Check your inbox.

Use only on systems you are authorized to test; capture evidence and include remediation.

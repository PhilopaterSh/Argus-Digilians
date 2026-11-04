# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

What should a web pentester know about Web Security for Developers — Compromising Authentication: Securing Password Resets?

## Analysis / Response

Based on Web Security for Developers (Securing Password Resets):

Securing Password Resets
Having a validated email address for each of your users allows you to handle
the (inevitable) scenario when a user forgets their password. Simply send
them an email with a password-reset link, containing a fresh validation token.
When the forgetful user opens the email and clicks the link, you can vali-
date the incoming token, and allow the user to choose a new password for
their account.
    Password-reset links should be short-lived, and should expire after
the user uses them. A good rule of thumb is to expire reset tokens after
30 minutes to prevent an attacker from abusing stale reset links. If an
attacker hacks a user’s email account, you can’t let them search for emails
containing reset links and then use those links to access your site under
the victim’s account.

Use only on systems you are authorized to test; capture evidence and include remediation.

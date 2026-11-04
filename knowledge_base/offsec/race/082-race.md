# RACE — portswigger_labs_sft

- source: portswigger_labs_sft
- class: race
- cwe: CWE-362

## Scenario

PortSwigger lab: "Bypassing rate limits via race conditions". This lab's login mechanism uses rate limiting to defend against brute-force attacks. However, this can be bypassed due to a race condition.

To solve the lab:

Work out how to exploit the race condition to bypass the rate limit.
Successfully brute-force the password for the user `carlos`.
Log in and access the admin panel.
Delete the user `carlos`.

You can log in to your account with the following credentials: `wiener:peter`.

You should use the following list of potential passwords:

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Race conditions: "Bypassing rate limits via race conditions".

## Solution steps

1. Experiment with the login function by intentionally submitting incorrect passwords for your own account.
2. Observe that if you enter the incorrect password more than three times, you're temporarily blocked from making any more login attempts for the same account.
3. Try logging in using another arbitrary username and observe that you see the normal `Invalid username or password` message. This indicates that the rate limit is enforced per-username rather than per-session.
4. Deduce that the number of failed attempts per username must be stored server-side.
5. Consider that there may be a race window between: When you submit the login attempt. When the website increments the counter for the number of failed login attempts associated with a particular username.

## Vulnerability note

Underlying issue: Race conditions (CWE-362). Use atomic operations, proper locking/transactions, and idempotency keys for sensitive state changes.

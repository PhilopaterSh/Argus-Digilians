# CRYPTO_WEAK — portswigger_labs_sft

- source: portswigger_labs_sft
- class: crypto_weak
- cwe: CWE-347

## Scenario

Scenario framing — PortSwigger "JWT authentication bypass via algorithm confusion" (JWT, Expert):
This lab uses a JWT-based mechanism for handling sessions. It uses a robust RSA key pair to sign and verify tokens. However, due to implementation flaws, this mechanism is vulnerable to algorithm confusion attacks.

To solve the lab, first obtain the server's public key. This is exposed via a standard endpoint. Use this key to sign a modified session token that gives you access to the admin panel at `/admin`, then delete the user `carlos`.

You can log in to your own account using the following credentials: `wiener:peter`

Tip

 We recommend familiarizing yourself with how to work with JWTs in Burp Suite before attempting this lab.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Expert) covers JWT: "JWT authentication bypass via algorithm confusion".

## Solution steps

1. In Burp, load the JWT Editor extension from the BApp store.
2. In the lab, log in to your own account and send the post-login `GET /my-account` request to Burp Repeater.
3. In Burp Repeater, change the path to `/admin` and send the request. Observe that the admin panel is only accessible when logged in as the `administrator` user.
4. In the browser, go to the standard endpoint `/jwks.json` and observe that the server exposes a JWK Set containing a single public key.
5. Copy the JWK object from inside the `keys` array. Make sure that you don't accidentally copy any characters from the surrounding array.

## Vulnerability note

Underlying issue: JWT (CWE-347). Verify signature and algorithm explicitly; reject alg=none; use strong secrets/keys and short expirations.

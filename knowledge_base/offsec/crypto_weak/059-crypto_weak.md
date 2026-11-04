# CRYPTO_WEAK — portswigger_labs_sft

- source: portswigger_labs_sft
- class: crypto_weak
- cwe: CWE-347

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: JWT authentication bypass via kid header path traversal
Topic: JWT
Level: Practitioner

Scenario:
This lab uses a JWT-based mechanism for handling sessions. In order to verify the signature, the server uses the `kid` parameter in JWT header to fetch the relevant key from its filesystem.

To solve the lab, forge a JWT that gives you access to the admin panel at `/admin`, then delete the user `carlos`.

You can log in to your own account using the following credentials: `wiener:peter`

Tip

 We recommend familiarizing yourself with how to work with JWTs in Burp Suite before attempting this lab.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers JWT: "JWT authentication bypass via kid header path traversal".

## Solution steps

1. In Burp, load the JWT Editor extension from the BApp store.
2. In the lab, log in to your own account and send the post-login `GET /my-account` request to Burp Repeater.
3. In Burp Repeater, change the path to `/admin` and send the request. Observe that the admin panel is only accessible when logged in as the `administrator` user.
4. Go to the JWT Editor Keys tab in Burp's main tab bar.
5. Click New Symmetric Key.
6. In the dialog, click Generate to generate a new key in JWK format. Note that you don't need to select a key size as this will automatically be updated later.
7. Replace the generated value for the `k` property with an empty string.
8. Click OK to save the key.

## Vulnerability note

Underlying issue: JWT (CWE-347). Verify signature and algorithm explicitly; reject alg=none; use strong secrets/keys and short expirations.

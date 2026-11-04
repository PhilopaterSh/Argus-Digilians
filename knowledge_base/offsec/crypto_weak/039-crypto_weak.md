# CRYPTO_WEAK — portswigger_labs_sft

- source: portswigger_labs_sft
- class: crypto_weak
- cwe: CWE-347

## Scenario

I'm stuck on the PortSwigger lab "JWT authentication bypass via jku header injection" (Practitioner, JWT). Here's the scenario:

This lab uses a JWT-based mechanism for handling sessions. The server supports the `jku` parameter in the JWT header. However, it fails to check whether the provided URL belongs to a trusted domain before fetching the key.

To solve the lab, forge a JWT that gives you access to the admin panel at `/admin`, then delete the user `carlos`.

You can log in to your own account using the following credentials: `wiener:peter`

Tip

 We recommend familiarizing yourself with how to work with JWTs in Burp Suite before attempting this lab.

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers JWT: "JWT authentication bypass via jku header injection".

## Solution steps

1. In Burp, load the JWT Editor extension from the BApp store.
2. In the lab, log in to your own account and send the post-login `GET /my-account` request to Burp Repeater.
3. In Burp Repeater, change the path to `/admin` and send the request. Observe that the admin panel is only accessible when logged in as the `administrator` user.
4. Go to the JWT Editor Keys tab in Burp's main tab bar.
5. Click New RSA Key.
6. In the dialog, click Generate to automatically generate a new key pair, then click OK to save the key. Note that you don't need to select a key size as this will automatically be updated later.
7. In the browser, go to the exploit server.
8. Replace the contents of the Body section with an empty JWK Set as follows: `{ "keys": [ ] }`
9. Back on the JWT Editor Keys tab, right-click on the entry for the key that you just generated, then select Copy Public Key as JWK.
10. Paste the JWK into the `keys` array on the exploit server, then store the exploit. The result should look something like this: `{ "keys": [ { "kty": "RSA", "e": "AQAB", "kid": "893d8f0b-061f-42c2-a4aa-5056e12b8ae7", "n": "yy1wpYmffgXBxhAUJzHHocCuJolwDqql75ZWuCQ_cb33K2vh9mk6GPM9gNN4Y_qTVX67WhsN3JvaFYw" } ] }`

## Vulnerability note

Underlying issue: JWT (CWE-347). Verify signature and algorithm explicitly; reject alg=none; use strong secrets/keys and short expirations.

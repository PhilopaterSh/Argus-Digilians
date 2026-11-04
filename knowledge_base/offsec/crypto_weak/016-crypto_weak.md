# CRYPTO_WEAK — portswigger_labs_sft

- source: portswigger_labs_sft
- class: crypto_weak
- cwe: CWE-347

## Scenario

PortSwigger lab: "JWT authentication bypass via weak signing key". This lab uses a JWT-based mechanism for handling sessions. It uses an extremely weak secret key to both sign and verify tokens. This can be easily brute-forced using a wordlist of common secrets.

To solve the lab, first brute-force the website's secret key. Once you've obtained this, use it to sign a modified session token that gives you access to the admin panel at `/admin`, then delete the user `carlos`.

You can log in to your own account using the following credentials: `wiener:peter`

Tip

 We recommend familiarizing yourself with how to work with JWTs in Burp Suite before attempting this lab.

 We also recommend using hashcat to brute-force the secret key. For details on how to do this, see Brute forcing secret keys using hashcat.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers JWT: "JWT authentication bypass via weak signing key".

## Solution steps

1. In Burp, load the JWT Editor extension from the BApp store.
2. In the lab, log in to your own account and send the post-login `GET /my-account` request to Burp Repeater.
3. In Burp Repeater, change the path to `/admin` and send the request. Observe that the admin panel is only accessible when logged in as the `administrator` user.
4. Copy the JWT and brute-force the secret. You can do this using hashcat as follows: ` hashcat -a 0 -m 16500 <YOUR-JWT> /path/to/jwt.secrets.list ` If you're using hashcat, this outputs the JWT, followed by the secret. If everything worked correctly, this should reveal that the weak secret is `secret1`.

## Vulnerability note

Underlying issue: JWT (CWE-347). Verify signature and algorithm explicitly; reject alg=none; use strong secrets/keys and short expirations.

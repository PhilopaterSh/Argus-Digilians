# CRYPTO_WEAK — portswigger_labs_sft

- source: portswigger_labs_sft
- class: crypto_weak
- cwe: CWE-347

## Scenario

Help me complete the lab "JWT authentication bypass via flawed signature verification" from PortSwigger Web Security Academy. Category: JWT. Difficulty: Apprentice.

This lab uses a JWT-based mechanism for handling sessions. The server is insecurely configured to accept unsigned JWTs.

To solve the lab, modify your session token to gain access to the admin panel at `/admin`, then delete the user `carlos`.

You can log in to your own account using the following credentials: `wiener:peter`

Tip

 We recommend familiarizing yourself with how to work with JWTs in Burp Suite before attempting this lab.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers JWT: "JWT authentication bypass via flawed signature verification".

## Solution steps

1. In the lab, log in to your own account.
2. In Burp, go to the Proxy > HTTP history tab and look at the post-login `GET /my-account` request. Observe that your session cookie is a JWT.
3. Double-click the payload part of the token to view its decoded JSON form in the Inspector panel. Notice that the `sub` claim contains your username. Send this request to Burp Repeater.
4. In Burp Repeater, change the path to `/admin` and send the request. Observe that the admin panel is only accessible when logged in as the `administrator` user.
5. Select the payload of the JWT again. In the Inspector panel, change the value of the `sub` claim to `administrator`, then click Apply changes.
6. Select the header of the JWT, then use the Inspector to change the value of the `alg` parameter to `none`. Click Apply changes.
7. In the message editor, remove the signature from the JWT, but remember to leave the trailing dot after the payload.
8. Send the request and observe that you have successfully accessed the admin panel.
9. In the response, find the URL for deleting `carlos` (`/admin/delete?username=carlos`). Send the request to this endpoint to solve the lab.

## Vulnerability note

Underlying issue: JWT (CWE-347). Verify signature and algorithm explicitly; reject alg=none; use strong secrets/keys and short expirations.

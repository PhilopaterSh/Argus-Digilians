# AUTH — portswigger_labs_sft

- source: portswigger_labs_sft
- class: auth
- cwe: CWE-287

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Authentication bypass via OAuth implicit flow
Topic: OAuth authentication
Level: Apprentice

Scenario:
This lab uses an OAuth service to allow users to log in with their social media account. Flawed validation by the client application makes it possible for an attacker to log in to other users' accounts without knowing their password.

To solve the lab, log in to Carlos's account. His email address is `carlos@carlos-montoya.net`.

You can log in with your own social media account using the following credentials: `wiener:peter`.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers OAuth authentication: "Authentication bypass via OAuth implicit flow".

## Solution steps

1. While proxying traffic through Burp, click "My account" and complete the OAuth login process. Afterwards, you will be redirected back to the blog website.
2. In Burp, go to "Proxy" > "HTTP history" and study the requests and responses that make up the OAuth flow. This starts from the authorization request `GET /auth?client_id=[...]`.
3. Notice that the client application (the blog website) receives some basic information about the user from the OAuth service. It then logs the user in by sending a `POST` request containing this information to its own `/authenticate` endpoint, along with the access token.
4. Send the `POST /authenticate` request to Burp Repeater. In Repeater, change the email address to `carlos@carlos-montoya.net` and send the request. Observe that you do not encounter an error.
5. Right-click on the `POST` request and select "Request in browser" > "In original session". Copy this URL and visit it in the browser. You are logged in as Carlos and the lab is solved.

## Vulnerability note

Underlying issue: OAuth authentication (CWE-287). Validate redirect_uri strictly, use the state parameter, and bind tokens to the correct client and user.

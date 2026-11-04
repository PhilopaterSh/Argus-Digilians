# SQLI — portswigger_labs_sft

- source: portswigger_labs_sft
- class: sqli
- cwe: CWE-943

## Scenario

PortSwigger lab: "Exploiting NoSQL operator injection to bypass authentication". The login functionality for this lab is powered by a MongoDB NoSQL database. It is vulnerable to NoSQL injection using MongoDB operators.

To solve the lab, log into the application as the `administrator` user.

You can log in to your own account using the following credentials: `wiener:peter`.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers NoSQL injection: "Exploiting NoSQL operator injection to bypass authentication".

## Solution steps

1. In Burp's browser, log in to the application using the credentials `wiener:peter`.
2. In Burp, go to Proxy > HTTP history. Right-click the `POST /login` request and select Send to Repeater.
3. In Repeater, test the username and password parameters to determine whether they allow you to inject MongoDB operators: Change the value of the `username` parameter from `"wiener"` to `{"$ne":""}`, then send the request. Notice that this enables you to log in. Change the value of the username parameter from `{"$ne":""}` to `{"$regex":"wien.*"}`, then send the request. Notice that you can also log in when using the `$regex` operator. With the username parameter set to `{"$ne":""}`, change the value of the password parameter from `"peter"` to `{"$ne":""}`, then send the request again. Notice that this causes the query to return an unexpected number of records. This indicates that more than one user has been selected.
4. With the password parameter set as `{"$ne":""}`, change the value of the username parameter to `{"$regex":"admin.*"},` then send the request again. Notice that this successfully logs you in as the admin user.
5. Right-click the response, then select Show response in browser. Copy the URL.
6. Paste the URL into Burp's browser to log in as the `administrator` user. The lab is solved.

## Vulnerability note

Underlying issue: NoSQL injection (CWE-943). Avoid concatenating user input into queries; use typed operators safely and validate input types.

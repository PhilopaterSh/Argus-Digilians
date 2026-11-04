# SQLI — portswigger_labs_sft

- source: portswigger_labs_sft
- class: sqli
- cwe: CWE-89

## Scenario

Help me complete the lab "SQL injection with filter bypass via XML encoding" from PortSwigger Web Security Academy. Category: SQL injection. Difficulty: Practitioner.

This lab contains a SQL injection vulnerability in its stock check feature. The results from the query are returned in the application's response, so you can use a UNION attack to retrieve data from other tables.

The database contains a `users` table, which contains the usernames and passwords of registered users. To solve the lab, perform a SQL injection attack to retrieve the admin user's credentials, then log in to their account.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers SQL injection: "SQL injection with filter bypass via XML encoding".

## Solution steps

1. Observe that the stock check feature sends the `productId` and `storeId` to the application in XML format.
2. Send the `POST /product/stock` request to Burp Repeater.
3. In Burp Repeater, probe the `storeId` to see whether your input is evaluated. For example, try replacing the ID with mathematical expressions that evaluate to other potential IDs, for example: `<storeId>1+1</storeId>`
4. Observe that your input appears to be evaluated by the application, returning the stock for different stores.
5. Try determining the number of columns returned by the original query by appending a `UNION SELECT` statement to the original store ID: `<storeId>1 UNION SELECT NULL</storeId>`
6. Observe that your request has been blocked due to being flagged as a potential attack.

## Vulnerability note

Underlying issue: SQL injection (CWE-89). Prevent SQLi with parameterized queries / prepared statements, strict input validation, and least-privilege DB accounts.

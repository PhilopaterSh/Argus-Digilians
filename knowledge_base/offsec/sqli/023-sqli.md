# SQLI — portswigger_labs_sft

- source: portswigger_labs_sft
- class: sqli
- cwe: CWE-89

## Scenario

PortSwigger lab: "SQL injection vulnerability in WHERE clause allowing retrieval of hidden data". This lab contains a SQL injection vulnerability in the product category filter. When the user selects a category, the application carries out a SQL query like the following:

`SELECT * FROM products WHERE category = 'Gifts' AND released = 1`

To solve the lab, perform a SQL injection attack that causes the application to display one or more unreleased products.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers SQL injection: "SQL injection vulnerability in WHERE clause allowing retrieval of hidden data".

## Solution steps

1. Use Burp Suite to intercept and modify the request that sets the product category filter.
2. Modify the `category` parameter, giving it the value `'+OR+1=1--`
3. Submit the request, and verify that the response now contains one or more unreleased products.

## Vulnerability note

Underlying issue: SQL injection (CWE-89). Prevent SQLi with parameterized queries / prepared statements, strict input validation, and least-privilege DB accounts.

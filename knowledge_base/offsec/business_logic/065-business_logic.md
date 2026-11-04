# BUSINESS_LOGIC — portswigger_labs_sft

- source: portswigger_labs_sft
- class: business_logic
- cwe: CWE-840

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Bypassing access controls using email address parsing discrepancies
Difficulty: Expert
Category: Business logic vulnerabilities

This lab validates email addresses to prevent attackers from registering addresses from unauthorized domains. There is a parser discrepancy in the validation logic and library used to parse email addresses.

To solve the lab, exploit this flaw to register an account and delete `carlos`.

Required knowledge

 To solve this lab, you'll need to understand the techniques described in the Splitting the Email Atom: Exploiting Parsers to Bypass Access Controls whitepaper by Gareth Heyes of the PortSwigger Research team.

## Analysis / Response

This PortSwigger Web Security Academy lab (Expert) covers Business logic vulnerabilities: "Bypassing access controls using email address parsing discrepancies".

## Solution steps

1. Open the lab and click Register.
2. Attempt to register an account with the email `foo@exploit-server.net`.
3. Notice that the application blocks the request and displays an error message stating that the email domain must be `ginandjuice.shop`. This indicates the server enforces a domain check during registration.

## Vulnerability note

Underlying issue: Business logic vulnerabilities (CWE-840). Validate workflow state server-side; never trust client-supplied prices, quantities, or step order.

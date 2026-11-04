# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

How do I test for SQL Injection: 2.3 Impact of SQL Injection on an in-scope web application?

## Analysis / Response

Based on Abhishek Pawar notes — SQL Injection Report (2.3 Impact of SQL Injection):

2.3 Impact of SQL Injection
Unauthorized access to sensitive data stored in the database, including user credentials and personal information
Authentication and authorization bypass, allowing attackers to impersonate legitimate users or gain administrative access
Disclosure of database structure, schema details, and application logic through query manipulation or error leakage
Modification or deletion of database records, leading to data integrity loss
Insertion of malicious or fraudulent data into the database
Complete compromise of the database server in severe cases, depending on database privileges
Escalation of application-level vulnerabilities into full system-level compromise Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).

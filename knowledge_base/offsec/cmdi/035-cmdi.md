# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-78

## Scenario

Explain Command Injection: 1.3 PHP Example with payloads/commands where the material provides them (authorized testing only).

## Analysis / Response

Based on Abhishek Pawar notes — Command Injection Report (1.3 PHP Example):

1.3 PHP Example

1.4 NodeJS Example

                                                                                    pg. 4

2. What is Command Injection Vulnerability ?
Command injection is a security flaw where an application executes unintended system
commands because it passes unsanitized user input to OS-level command execution
functions, allowing an attacker to run arbitrary commands on the server.

The filename parameter is directly passed from the GET request to the system() function in
PHP, which is intended to create a .pdf file for the user. However, if an attacker appends
additional characters or command sequences to the filename parameter, and proper input
validation and sanitization are not implemented, those injected strings will also be passed
to the command-executing function. As a result, the operating system interprets and
executes the injected commands along with the intended file-creation command, leading
to a command injection vulnerability.

                                                                                       pg. 5

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

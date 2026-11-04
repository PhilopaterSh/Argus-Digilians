# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Web Application Hacker's Handbook 2e — Chapter 10 n Attacking Back-End Components                  387

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Chapter 10 n Attacking Back-End Components                  387):

Because XML is an interpreted language, SOAP is potentially vulnerable to
               code injection in a similar way as the other examples already described. XML
               elements are represented syntactically, using the metacharacters <, >, and /. If
               user-supplied data containing these characters is inserted directly into a SOAP
               message, an attacker may be able to interfere with the message’s structure and
               therefore interfere with the application’s logic or cause other undesirable effects.
                  Consider a banking application in which a user initiates a funds transfer
               using an HTTP request like the following:
                 POST /bank/27/Default.aspx HTTP/1.0
                 Host: mdsec.net
                 Content-Length: 65

                 FromAccount=18281008&Amount=1430&ToAccount=08447656&Submit=Submit

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).

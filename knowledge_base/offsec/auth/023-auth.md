# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

I'm preparing a bug bounty test plan covering Web Application Hacker's Handbook 2e — Chapter 2 n Core Defense Mechanisms                 23. What does the source recommend?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Chapter 2 n Core Defense Mechanisms                 23):

cases, the application should reject the request and log the incident for potential
              investigation (see the “Handling Attackers” section later in this chapter).

              Approaches to Input Handling
              Various broad approaches are commonly taken to the problem of handling
              user input. Different approaches are often preferable for different situations
              and different types of input, and a combination of approaches may sometimes
              be desirable.

              “Reject Known Bad”
              This approach typically employs a blacklist containing a set of literal strings or
              patterns that are known to be used in attacks. The validation mechanism blocks
              any data that matches the blacklist and allows everything else.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).

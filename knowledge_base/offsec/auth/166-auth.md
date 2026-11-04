# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Summarize how to identify, exploit (safely), and remediate issues related to: Web Application Hacker's Handbook 2e — Maintaining Audit Logs

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Maintaining Audit Logs):

Maintaining Audit Logs
              Audit logs are valuable primarily when investigating intrusion attempts against
              an application. Following such an incident, effective audit logs should enable
              the application’s owners to understand exactly what has taken place, which
              vulnerabilities (if any) were exploited, whether the attacker gained unauthorized
              access to data or performed any unauthorized actions, and, as far as possible,
              provide evidence of the intruder’s identity.

c02.indd 31                                                                                         8/19/2011 12:02:43 PM

                                                                             Stuttard c02.indd V3 - 07/22/2011 Page 32

          32   Chapter 2 n Core Defense Mechanisms

                 In any application for which security is important, key events should be logged
               as a matter of course. At a minimum, these typically include the following:
                  n   All events relating to the authentication functionality, such as successful
                      and failed login, and change of password
                  n   Key transactions, such as credit card payments and funds transfers
                  n   Access attempts that are blocked by the access control mechanisms
                  n   Any requests containing known attack strings that indicate overtly mali-
                      cious intentions

# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

I'm preparing a bug bounty test plan covering Web Application Hacker's Handbook 2e — Vulnerable Transmission of Credentials. What does the source recommend?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Vulnerable Transmission of Credentials):

Vulnerable Transmission of Credentials
               If an application uses an unencrypted HTTP connection to transmit login cre-
               dentials, an eavesdropper who is suitably positioned on the network can, of
               course, intercept them. Depending on the user’s location, potential eavesdrop-
               pers may reside:
                  n   On the user’s local network
                  n   Within the user’s IT department
                  n   Within the user’s ISP
                  n   On the Internet backbone
                  n   Within the ISP hosting the application
                  n   Within the IT department managing the application

c06.indd 169                                                                                          8/19/2011 12:06:38 PM

                                                                         Stuttard c06.indd V3 - 07/22/2011 Page 170

          170   Chapter 6 n Attacking Authentication

                  NOTE Any of these locations may be occupied by authorized personnel but
                  also potentially by an external attacker who has compromised the relevant
                  infrastructure through some other means. Even if the intermediaries on a par-
                  ticular network are believed to be trusted, it is safer to use secure transport
                  mechanisms when passing sensitive data over it.

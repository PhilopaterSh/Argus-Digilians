# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Walk me through Web Application Hacker's Handbook 2e — 11.7 Test for Web Application Firewalling with practical steps and examples from the source material.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (11.7 Test for Web Application Firewalling):

11.7 Test for Web Application Firewalling
                11.7.1 Submit an arbitrary parameter name to the application with a clear attack
                       payload in the value, ideally somewhere the application includes the
                       name and/or value in the response. If the application blocks the attack,
                       this is likely to be due to an external defense.
                11.7.2 If a variable can be submitted that is returned in a server response, submit
                       a range of fuzz strings and encoded variants to identify the behavior of
                       the application defenses to user input.
                11.7.3 Conﬁrm this behavior by performing the same attacks on variables
                       within the application.
                11.7.4 For all fuzzing strings and requests, use payload strings that are unlikely
                       to exist in a standard signature database. Although giving examples of

c21.indd 848                                                                                           8/19/2011 12:22:06 PM

                                                                     Stuttard c21.indd V3 - 08/16/2011 Page 849

                                        Chapter 21 n A Web Application Hacker’s Methodology             849

                      these is by deﬁnition impossible, avoid using /etc/passwd or /windows/
                      system32/config/sam as payloads for ﬁle retrieval. Also avoid using
                      terms such as <script> in an XSS attack and using alert() or xss as
                      XSS payloads.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

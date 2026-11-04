# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

I'm preparing a bug bounty test plan covering Web Application Hacker's Handbook 2e — 176   Chapter 6 n Attacking Authentication. What does the source recommend?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (176   Chapter 6 n Attacking Authentication):

176   Chapter 6 n Attacking Authentication

                “Remember Me” Functionality
                Applications often implement “remember me” functions as a convenience to
                users. This way, users don’t need to reenter their username and password each
                time they use the application from a speciﬁc computer. These functions are
                often insecure by design and leave the user exposed to attack both locally and
                by users on other computers:
                   n   Some “remember me” functions are implemented using a simple per-
                       sistent cookie, such as RememberUser=daf (see Figure 6-6). When this
                       cookie is submitted to the initial application page, the application trusts
                       the cookie to authenticate the user, and it creates an application session
                       for that person, bypassing the login. An attacker can use a list of common
                       or enumerated usernames to gain full access to the application without
                       any authentication.

                Figure 6-6: A vulnerable “remember me” function, which automatically logs in a
                user based solely on a username stored in a cookie

c06.indd 176                                                                                              8/19/2011 12:06:39 PM

                                                                  Stuttard c06.indd V3 - 07/22/2011 Page 177

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

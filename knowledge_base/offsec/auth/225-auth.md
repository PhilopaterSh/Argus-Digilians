# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

How do I test for Web Application Hacker's Handbook 2e — Prevent Misuse of the Account Recovery Function on an in-scope web application?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Prevent Misuse of the Account Recovery Function):

Prevent Misuse of the Account Recovery Function
                 n   In the most security-critical applications, such as online banking, account
                     recovery in the event of a forgotten password is handled out-of-band. A
                     user must make a telephone call and answer a series of security questions,
                     and new credentials or a reactivation code are also sent out-of-band (via
                     conventional mail) to the user’s registered home address. The majority of
                     applications do not want or need this level of security, so an automated
                     recovery function may be appropriate.

c06.indd 199                                                                                         8/19/2011 12:06:42 PM

                                                                         Stuttard c06.indd V3 - 07/22/2011 Page 200

          200   Chapter 6 n Attacking Authentication

                  n   A well-designed password recovery mechanism needs to prevent accounts
                      from being compromised by an unauthorized party and minimize any
                      disruption to legitimate users.
                  n   Features such as password “hints” should never be used, because they
                      mainly help an attacker trawl for accounts that have obvious hints set.
                  n   The best automated solution for enabling users to regain control of accounts
                      is to e-mail the user a unique, time-limited, unguessable, single-use recov-
                      ery URL. This e-mail should be sent to the address that the user provided
                      during registration. Visiting the URL allows the user to set a new pass-
                      word. After this has been done, a second e-mail should be sent, indicating
                      that a password change was made. To prevent an attacker from denying
                      service to users by continually requesting password reactivation e-mails,
                      the user’s existing credentials should remain valid until they are changed.
                  n   To further protect against unauthorized access, applications may present
                      users with a secondary challenge that they must complete before gain-
                      ing access to the password reset function. Be sure that the design of this
                      challenge does not introduce new vulnerabilities:

                      n   The challenge should implement the same question or set of ques-
                          tions for everyone, mandated by the application during registration.

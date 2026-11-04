# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

How do I test for Web Application Hacker's Handbook 2e — Prevent Brute-Force Attacks on an in-scope web application?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Prevent Brute-Force Attacks):

Prevent Brute-Force Attacks
                  n   Measures need to be enforced within all the various challenges imple-
                      mented by the authentication functionality to prevent attacks that attempt
                      to meet those challenges using automation. This includes the login itself,

c06.indd 196                                                                                           8/19/2011 12:06:41 PM

                                                              Stuttard c06.indd V3 - 07/22/2011 Page 197

                                                    Chapter 6 n Attacking Authentication            197

                   as well as functions to change the password, to recover from a forgotten
                   password situation, and the like.
               n   Using unpredictable usernames and preventing their enumeration presents
                   a signiﬁcant obstacle to completely blind brute-force attacks and requires
                   an attacker to have somehow discovered one or more speciﬁc usernames
                   before mounting an attack.
               n   Some security-critical applications (such as online banks) simply disable
                   an account after a small number of failed logins (such as three). They also
                   require that the account owner take various out-of-band steps to reactivate
                   the account, such as telephoning customer support and answering a series
                   of security questions. Disadvantages of this policy are that it allows an
                   attacker to deny service to legitimate users by repeatedly disabling their
                   accounts, and the cost of providing the account recovery service. A more
                   balanced policy, suitable for most security-aware applications, is to sus-
                   pend accounts for a short period (such as 30 minutes) following a small
                   number of failed login attempts (such as three). This serves to massively
                   slow down any password-guessing attack, while mitigating the risk of
                   denial-of-service attacks and also reducing call center work.
               n   If a policy of temporary account suspension is implemented, care should
                   be taken to ensure its effectiveness:

                   n   To prevent information leakage leading to username enumeration, the
                       application should never indicate that any speciﬁc account has been
                       suspended. Rather, it should respond to any series of failed logins,
                       even those using an invalid username, with a message advising that
                       accounts are suspended if multiple failures occur and that the user
                       should try again later (as just discussed).
                   n   The policy’s metrics should not be disclosed to users. Simply telling
                       legitimate users to “try again later” does not seriously diminish their
                       quality of service. But informing an attacker exactly how many failed
                       attempts are tolerated, and how long the suspension period is, enables
                       him to optimize any attempt to continue guessing passwords in spite
                       of the policy.
                   n   If an account is suspended, login attempts should be rejected without
                       even checking the credentials. Some applications that have imple-
                       mented a suspension policy remain vulnerable to brute-forcing because
                       they continue to fully process login attempts during the suspension
                       period, and they return a subtly (or not so subtly) different mes-
                       sage when valid credentials are submitted. This behavior enables
                       an effective brute-force attack to proceed at full speed regardless of
                       the suspension policy.

c06.indd 197                                                                                     8/19/2011 12:06:42 PM

                                                                         Stuttard c06.indd V3 - 07/22/2011 Page 198

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

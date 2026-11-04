# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-284

## Scenario

I'm preparing a bug bounty test plan covering Web Application Hacker's Handbook 2e — Because of the complex nature of typical access control requirements, this. What does the source recommend?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Because of the complex nature of typical access control requirements, this):

Because of the complex nature of typical access control requirements, this
               mechanism is a frequent source of security vulnerabilities that enable an attacker

c02.indd 20                                                                                           8/19/2011 12:02:42 PM

                                                                    Stuttard c02.indd V3 - 07/22/2011 Page 21

                                                       Chapter 2 n Core Defense Mechanisms             21

              to gain unauthorized access to data and functionality. Developers often make
              ﬂawed assumptions about how users will interact with the application and
              frequently make oversights by omitting access control checks from some appli-
              cation functions. Probing for these vulnerabilities is often laborious, because
              essentially the same checks need to be repeated for each item of functionality.
              Because of the prevalence of access control ﬂaws, however, this effort is always
              a worthwhile investment when you are attacking a web application. Chapter
              8 describes how you can automate some of the effort involved in performing
              rigorous access control testing.

              Figure 2-3: An application enforcing access control

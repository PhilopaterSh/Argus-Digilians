# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Web Application Hacker's Handbook 2e — Introduction

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Introduction):

(see Chapter 3 for more details). The traditional web spider’s URL-based view
                of the application is useful in these situations. In the EIS application, the
                /shop and /pub paths employ REST-style URLs, and spidering these areas eas-
                ily provides unique links to the items available within these paths.

              Figure 4-1: Mapping part of an application using Burp Spider

                Although it can often be effective, this kind of fully automated approach to
              content enumeration has some signiﬁcant limitations:
                 n   Unusual navigation mechanisms (such as menus dynamically created
                     and handled using complicated JavaScript code) often are not handled
                     properly by these tools, so they may miss whole areas of an application.
                 n   Links buried within compiled client-side objects such as Flash or Java
                     applets may not be picked up by a spider.
                 n   Multistage functionality often implements ﬁne-grained input validation
                     checks, which do not accept the values that may be submitted by an auto-
                     mated tool. For example, a user registration form may contain ﬁelds for
                     name, e-mail address, telephone number, and zip code. An automated

c04.indd 75                                                                                      8/19/2011 12:04:41 PM

                                                                  Stuttard c04.indd V3 - 07/22/2011 Page 76

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

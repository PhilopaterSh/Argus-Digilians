# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Summarize how to identify, exploit (safely), and remediate issues related to: Web Application Hacker's Handbook 2e — Using the automated content discovery techniques already described, it

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Using the automated content discovery techniques already described, it):

Using the automated content discovery techniques already described, it
               is possible to request a large number of common ﬁle extensions and quickly
               conﬁrm whether any of the associated technologies are implemented on the
               server.
                  The divergent behavior described arises because many web servers map
               speciﬁc ﬁle extensions to particular server-side components. Each different
               component may handle errors (including requests for nonexistent content) dif-
               ferently. Figure 4-14 shows the various extensions that are mapped to different
               handler DLLs in a default installation of IIS 5.0.

c04.indd 103                                                                                             8/19/2011 12:04:45 PM

                                                                   Stuttard c04.indd V3 - 07/22/2011 Page 104

          104   Chapter 4 n Mapping the Application

                Figure 4-13: A generic error message created when an unrecognized file extension is
                requested

                Figure 4-14: File extension mappings in IIS 5.0

                   It is possible to detect the presence of each ﬁle extension mapping via the
                different error messages generated when that ﬁle extension is requested. In
                some cases, discovering a particular mapping may indicate the presence of a
                web server vulnerability. For example, the .printer and .ida/.idq handlers
                in IIS have in the past been found vulnerable to buffer overﬂow vulnerabilities.
                   Another common ﬁngerprint to be aware of are URLs that look like this:
                  https://wahh-app/news/0,,2-421206,00.html

c04.indd 104                                                                                            8/19/2011 12:04:45 PM

                                                          Stuttard c04.indd V3 - 07/22/2011 Page 105

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

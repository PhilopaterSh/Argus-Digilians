# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-284

## Scenario

Walk me through Web Application Hacker's Handbook 2e — 6.4.2 Some applications base access control decisions on the HTTP Referer with practical steps and examples from the source material.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (6.4.2 Some applications base access control decisions on the HTTP Referer):

6.4.2 Some applications base access control decisions on the HTTP Referer
                     header. For example, an application may properly control access to
                     /admin.jsp and accept any request showing this as its Referer. To test
                     for this behavior, attempt to perform some privileged actions to which
                     you are authorized, and submit a missing or modiﬁed Referer header.
                     If this change causes the application to block your request, it may be
                     using the Referer header in an unsafe way. Try performing the same
                     action as an unauthorized user, but supply the original Referer header
                     and see whether the action succeeds.
               6.4.3 If HEAD is an allowed method on the site, test for insecure container-
                     managed access control to URLs. Make a request using the HEAD method
                     to determine whether the application permits it.

c21.indd 823                                                                                       8/19/2011 12:22:03 PM

                                                                                               Stuttard c21.indd V3 - 08/16/2011 Page 824

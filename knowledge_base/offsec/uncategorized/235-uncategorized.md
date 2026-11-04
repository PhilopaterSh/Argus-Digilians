# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do I test for Web Application Hacker's Handbook 2e — 5.10.5 Identify all the possible domain names and paths that will receive the on an in-scope web application?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (5.10.5 Identify all the possible domain names and paths that will receive the):

5.10.5 Identify all the possible domain names and paths that will receive the
                      cookies that the application issues. Establish whether any other web
                      applications are accessible via these domain names or paths that you
                      may be able to leverage to capture the cookies issued to users of the
                      target application.

               6          Test Access Controls

                                                                 6.4. Test for
                     6.1. Understand the requirements
                                                              insecure methods

                 6.2. Test with           6.3. Test with
                multiple accounts        limited access

               Figure 21-7: Testing access controls

               6.1        Understand the Access Control Requirements
                6.1.1 Based on the core functionality implemented within the application,
                      understand the broad requirements for access control in terms of verti-
                      cal segregation (different levels of users have access to different types
                      of functionality) and horizontal segregation (users at the same privilege
                      level have access to different subsets of data). Often, both types of seg-
                      regation are present. For example, ordinary users may be able to access
                      their own data, while administrators can access everyone’s data.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

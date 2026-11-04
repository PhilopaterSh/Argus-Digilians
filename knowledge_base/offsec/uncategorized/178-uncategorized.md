# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do I test for Web Application Hacker's Handbook 2e — Searching a large codebase for comments indicating common problems is on an in-scope web application?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Searching a large codebase for comments indicating common problems is):

Searching a large codebase for comments indicating common problems is
               frequently an effective source of low-hanging fruit. Here are some search terms
               that have proven useful:
                  n   bug
                  n   problem
                  n   bad
                  n   hope
                  n   todo
                  n   fix
                  n   overflow
                  n   crash
                  n   inject
                  n   xss
                  n   trust

               The Java Platform
               This section describes ways to acquire user-supplied input, ways to interact with
               the user’s session, potentially dangerous APIs, and security-relevant conﬁgura-
               tion options on the Java platform.

               Identifying User-Supplied Data
               Java applications acquire user-submitted input via the javax.servlet.http.
               HttpServletRequest interface, which extends the javax.servlet.ServletRequest
               interface. These two interfaces contain numerous APIs that web applications
               can use to access user-supplied data. The APIs listed in Table 19-1 can be used
               to obtain data from the user request.

c19.indd 711                                                                                       8/19/2011 12:18:34 PM

                                                                         Stuttard c19.indd V2 - 08/11/2011 Page 712

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

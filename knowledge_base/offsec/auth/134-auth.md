# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-384

## Scenario

I'm preparing a bug bounty test plan covering Web Application Hacker's Handbook 2e — Per-Page Tokens. What does the source recommend?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Per-Page Tokens):

Per-Page Tokens
                Finer-grained control over sessions can be achieved, and many kinds of session
                attacks can be made more difﬁcult or impossible, by using per-page tokens in
                addition to session tokens. Here, a new page token is created every time a user
                requests an application page (as opposed to an image, for example) and is passed
                to the client in a cookie or a hidden ﬁeld of an HTML form. Each time the user
                makes a request, the page token is validated against the last value issued, in
                addition to the normal validation of the main session token. In the case of a
                non-match, the entire session is terminated. Many of the most security-critical
                web applications on the Internet, such as online banks, employ per-page tokens
                to provide increased protection for their session management mechanism, as
                shown in Figure 7-12.

                Figure 7-12: Per-page tokens used in a banking application

                  The use of per-page tokens does impose some restrictions on navigation (for
                example, on use of the back and forward buttons and multiwindow browsing).

c07.indd 252                                                                                                8/19/2011 12:07:44 PM

                                                                 Stuttard c07.indd V3 - 07/22/2011 Page 253

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

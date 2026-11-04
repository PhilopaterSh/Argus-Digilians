# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Explain Web Application Hacker's Handbook 2e — However, there may still be situations where a fully automated approach with payloads/commands where the material provides them (authorized testing only).

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (However, there may still be situations where a fully automated approach):

However, there may still be situations where a fully automated approach
                     is not completely effective. We discuss approaches to mapping this kind
                     of functionality later in this chapter.
                 n   Conversely to the previous point, some applications place volatile data
                     within URLs that is not actually used to identify resources or functions (for
                     example, parameters containing timers or random number seeds). Each
                     page of the application may contain what appears to be a new set of URLs
                     that the spider must request, causing it to continue running indeﬁnitely.
                 n   Where an application uses authentication, an effective application spider
                     must be able to handle this to access the functionality that the authen-
                     tication protects. The spiders mentioned previously can achieve this by
                     manually conﬁguring the spider either with a token for an authenticated
                     session or with credentials to submit to the login function. However, even
                     when this is done, it is common to ﬁnd that the spider’s operation breaks
                     the authenticated session for various reasons:

                     n   By following all URLs, at some point the spider will request the logout
                         function, causing its session to break.
                     n   If the spider submits invalid input to a sensitive function, the applica-
                         tion may defensively terminate the session.
                     n   If the application uses per-page tokens, the spider almost certainly will
                         fail to handle these properly by requesting pages out of their expected
                         sequence, probably causing the entire session to be terminated.

c04.indd 76                                                                                           8/19/2011 12:04:41 PM

                                                              Stuttard c04.indd V3 - 07/22/2011 Page 77

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Web Application Hacker's Handbook 2e — 712   Chapter 19 n Finding Vulnerabilities in Source Code

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (712   Chapter 19 n Finding Vulnerabilities in Source Code):

712   Chapter 19 n Finding Vulnerabilities in Source Code

                Table 19-1: APIs Used to Acquire User-Supplied Data on the Java Platform

                  API                           DESCRIPTION
                  getParameter                  Parameters within the URL query string and the body
                                                of a POST request are stored as a map of String
                  getParameterNames             names to String values, which can be accessed
                  getParameterValues            using these APIs.

                  getParameterMap
                  getQueryString                Returns the entire query string contained within the
                                                request and can be used as an alternative to the
                                                getParameter APIs.
                  getHeader                     HTTP headers in the request are stored as a map
                                                of String names to String values and can be
                  getHeaders                    accessed using these APIs.
                  getHeaderNames
                  getRequestURI                 These APIs return the URL contained within the
                                                request, including the query string.
                  getRequestURL
                  getCookies                    Returns an array of Cookie objects, which contain
                                                details of the cookies received in the request, includ-
                                                ing their names and values.
                  getRequestedSessionId         Used as an alternative to getCookies in some
                                                cases; returns the session ID value submitted within
                                                the request.
                  getInputStream                These APIs return different representations of the
                                                raw request received from the client and there-
                  getReader                     fore can be used to access any of the information
                                                obtained by all the other APIs.
                  getMethod                     Returns the method used in the HTTP request.
                  getProtocol                   Returns the protocol used in the HTTP request.
                  getServerName                 Returns the value of the HTTP Host header.
                  getRemoteUser                 If the current user is authenticated, these APIs return
                                                details of the user, including his login name. If users
                  getUserPrincipal              can choose their own username during self-registra-
                                                tion, this may be a means of introducing malicious
                                                input into the application’s processing.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

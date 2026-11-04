# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Explain Web Application Hacker's Handbook 2e — HTTP Responses with payloads/commands where the material provides them (authorized testing only).

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (HTTP Responses):

HTTP Responses
              A typical HTTP response is as follows:

                HTTP/1.1 200 OK
                Date: Tue, 19 Apr 2011 09:23:32 GMT
                Server: Microsoft-IIS/6.0
                X-Powered-By: ASP.NET
                Set-Cookie: tracking=tI8rk7joMx44S2Uu85nSWc
                X-AspNet-Version: 2.0.50727
                Cache-Control: no-cache
                Pragma: no-cache
                Expires: Thu, 01 Jan 1970 00:00:00 GMT
                Content-Type: text/html; charset=utf-8
                Content-Length: 1067

                <!DOCTYPE html PUBLIC “-//W3C//DTD XHTML 1.0 Transitional//EN” “http://
                www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd”><html xmlns=”http://
                www.w3.org/1999/xhtml” ><head><title>Your details</title>
                ...

c03.indd 41                                                                                           8/19/2011 12:03:43 PM

                                                                         Stuttard c03.indd V3 - 07/22/2011 Page 42

          42   Chapter 3 n Web Application Technologies

                 The ﬁrst line of every HTTP response consists of three items, separated by
               spaces:
                  n   The HTTP version being used.
                  n   A numeric status code indicating the result of the request. 200 is the most
                      common status code; it means that the request was successful and that
                      the requested resource is being returned.
                  n   A textual “reason phrase” further describing the status of the response. This
                      can have any value and is not used for any purpose by current browsers.
                 Here are some other points of interest in the response:
                  n   The Server header contains a banner indicating the web server software
                      being used, and sometimes other details such as installed modules and
                      the server operating system. The information contained may or may not
                      be accurate.
                  n   The Set-Cookie header issues the browser a further cookie; this is sub-
                      mitted back in the Cookie header of subsequent requests to this server.
                  n   The Pragma header instructs the browser not to store the response in its
                      cache. The Expires header indicates that the response content expired
                      in the past and therefore should not be cached. These instructions are
                      frequently issued when dynamic content is being returned to ensure
                      that browsers obtain a fresh version of this content on subsequent
                      occasions.
                  n   Almost all HTTP responses contain a message body following the blank
                      line after the headers. The Content-Type header indicates that the body
                      of this message contains an HTML document.
                  n   The Content-Length header indicates the length of the message body in
                      bytes.

               HTTP Methods

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

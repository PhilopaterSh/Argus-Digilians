# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Explain Web Application Hacker's Handbook 2e — 100   Chapter 4 n Mapping the Application with payloads/commands where the material provides them (authorized testing only).

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (100   Chapter 4 n Mapping the Application):

100   Chapter 4 n Mapping the Application

                HTTP Headers
                Many applications perform custom logging functions and may log the contents
                of HTTP headers such as Referer and User-Agent. These headers should always
                be considered as possible entry points for input-based attacks.
                   Some applications perform additional processing on the Referer header. For
                example, an application may detect that a user has arrived via a search engine,
                and seek to provide a customized response tailored to the user’s search query.
                The application may echo the search term or may attempt to highlight matching
                expressions within the response. Some applications seek to boost their search
                rankings by dynamically adding content such as HTML keywords, containing
                strings that recent visitors from search engines have been searching for. In this
                situation, it may be possible to persistently inject content into the application’s
                responses by making a request numerous times containing a suitably crafted
                Referer URL.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

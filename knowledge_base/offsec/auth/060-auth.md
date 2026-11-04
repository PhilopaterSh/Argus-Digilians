# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe the methodology and key techniques for Web Application Hacker's Handbook 2e — 2.2.3 Identify any out-of-band channels via which user-controllable or other during an authorized assessment.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (2.2.3 Identify any out-of-band channels via which user-controllable or other):

2.2.3 Identify any out-of-band channels via which user-controllable or other
                     third-party data is being introduced into the application’s processing.
                     An example is a web mail application that processes and renders mes-
                     sages received via SMTP.

               2.3    Identify the Technologies Used
               2.3.1 Identify each of the different technologies used on the client side, such as
                     forms, scripts, cookies, Java applets, ActiveX controls, and Flash objects.
               2.3.2 As far as possible, establish which technologies are being used on the
                     server side, including scripting languages, application platforms, and
                     interaction with back-end components such as databases and e-mail
                     systems.
               2.3.3 Check the HTTP Server header returned in application responses, and
                     also check for any other software identiﬁers contained within custom
                     HTTP headers or HTML source code comments. Note that in some cases,
                     different areas of the application are handled by different back-end
                     components, so different banners may be received.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

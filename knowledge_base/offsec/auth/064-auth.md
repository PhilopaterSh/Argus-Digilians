# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Explain Web Application Hacker's Handbook 2e — The preceding request contains a header specifying that the type of content in with payloads/commands where the material provides them (authorized testing only).

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (The preceding request contains a header specifying that the type of content in):

The preceding request contains a header specifying that the type of content in
              the message body is x-www-form-urlencoded. This means that parameters are
              represented in the message body as name/value pairs in the same way as they
              are in the URL query string. The other content type you are likely to encoun-
              ter when form data is submitted is multipart/form-data. An application can
              request that browsers use multipart encoding by specifying this in an enctype
              attribute in the form tag. With this form of encoding, the Content-Type header
              in the request also speciﬁes a random string that is used as a separator for the

c03.indd 59                                                                                         8/19/2011 12:03:45 PM

                                                                       Stuttard c03.indd V3 - 07/22/2011 Page 60

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do I test for Web Application Hacker's Handbook 2e — This request causes the back-end server to check whether cleared funds are on an in-scope web application?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (This request causes the back-end server to check whether cleared funds are):

This request causes the back-end server to check whether cleared funds are
               available to perform the transfer and, if so, to carry it out. However, the front-
               end server can optionally specify that cleared funds are available, and therefore
               bypass the check, by supplying the following parameter:
                 clearedfunds=true

                  If the attacker is aware of this behavior, he can attempt to perform an HPI
               attack to inject the clearedfunds parameter into the back-end request. To do
               this, he adds the required parameter onto the end of an existing parameter’s
               value and URL-encodes the characters & and =, which are used to separate
               names and values:
                 POST /bank/48/Default.aspx HTTP/1.0
                 Host: mdsec.net
                 Content-Length: 96

                 FromAccount=18281008&Amount=1430&ToAccount=08447656%26clearedfunds%3dtru
                 e&Submit=Submit

c10.indd 393                                                                                        8/19/2011 12:10:49 PM

                                                                         Stuttard c10.indd V2 - 07/05/2011 Page 394

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

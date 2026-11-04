# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Web Application Hacker's Handbook 2e — ServerName eis

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (ServerName eis):

ServerName eis
                        DocumentRoot /var/www2
                      </VirtualHost>

                       In addition to the DocumentRoot directive, virtual host containers can be used
                    to specify other conﬁguration options for the website in question. A common con-
                    ﬁguration mistake is to overlook the default host so that any security conﬁguration
                    applies to only a virtual host and can be bypassed when the default host is accessed.

                      HACK STEPS

                        1. Submit GET requests to the root directory using the following:
                            n The correct Host header.
                            n An arbitrary Host header.
                            n The server’s IP address in the Host header.
                            n No Host header.
                        2. Compare the responses to these requests. For example, when an IP
                           address is used in the Host header, the server may simply respond with
                           a directory listing. You may also find that different default content is
                           accessible.
                        3. If you observe different behavior, repeat your application mapping exer-
                           cises using the Host header that generated different results. Be sure to
                           perform a Nikto scan using the -vhost option to identify any default con-
                           tent that may have been overlooked during initial application mapping.

     c18.indd 683                                                                                           8/19/2011 12:17:53 PM

                                                                             Stuttard c18.indd V2 - 07/28/2011 Page 684

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Walk me through Web Application Hacker's Handbook 2e — Chapter 10 n Attacking Back-End Components                365 with practical steps and examples from the source material.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Chapter 10 n Attacking Back-End Components                365):

In some cases, it may not be possible to inject an entirely separate com-
               mand due to ﬁltering of required characters or the behavior of the command
               API being used by the application. Nevertheless, it may still be possible to
               interfere with the behavior of the command being performed to achieve
               some desired result.
                 In one instance seen by the authors, the application passed user input
               to the operating system command nslookup to ﬁ nd the IP address of a
               domain name supplied by the user. The metacharacters needed to inject new
               commands were being blocked, but the < and > characters used to redirect
               the command’s input and output were allowed. The nslookup command
               usually outputs the IP address for a domain name, which did not seem to
               provide an effective attack vector. However, if an invalid domain name is
               supplied, the command outputs an error message that includes the domain
               name that was looked up. This behavior proved sufﬁcient to deliver a
               serious attack:
                  n   Submit a fragment of server-executable script code as the domain name
                      to be resolved. The script can be encapsulated in quotes to ensure that
                      the command interpreter treats it as a single token.
                  n   Use the > character to redirect the command’s output to a ﬁle in an execut-
                      able folder within the web root. The command executed by the operating
                      system is as follows:
                      nslookup “[script code]” > [/path/to/executable_file]

                  n   When the command is run, the following output is redirected to the execut-
                      able ﬁle:
                      ** server can’t find [script code]: NXDOMAIN

                  n   This ﬁle can then be invoked using a browser, and the injected script
                      code is executed on the server. Because most scripting languages allow
                      pages to contain a mix of client-side content and server-side markup,
                      the parts of the error message that the attacker does not control are
                      just treated as plain text, and the markup within the injected script is
                      executed. The attack therefore succeeds in leveraging a restricted com-
                      mand injection condition to introduce an unrestricted backdoor into the
                      application server.

                 TRY IT!

                           http://mdsec.net/admin/18/

c10.indd 365                                                                                        8/19/2011 12:10:47 PM

                                                                         Stuttard c10.indd V2 - 07/05/2011 Page 366

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

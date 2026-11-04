# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Summarize how to identify, exploit (safely), and remediate issues related to: Web Application Hacker's Handbook 2e — 788   Chapter 20 n A Web Application Hacker’s Toolkit

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (788   Chapter 20 n A Web Application Hacker’s Toolkit):

788   Chapter 20 n A Web Application Hacker’s Toolkit

                  TRY IT!

                            http://mdsec.net/addressbook/32/

                  In addition to built-in commands and libraries, you can call out to various
                simple tools and utilities from Perl scripts and operating system shell scripts.
                Some tools that are useful for this purpose are described next.

                Wget
                Wget is a handy tool for retrieving a speciﬁed URL using HTTP or HTTPS.
                It can support a downstream proxy, HTTP authentication, and various other
                conﬁguration options.

                Curl
                Curl is one of the most ﬂexible command-line tools for issuing HTTP and HTTPS
                requests. It supports GET and POST methods, request parameters, client SSL
                certiﬁcates, and HTTP authentication. In the following example, the page title
                is retrieved for page ID values between 10 and 40:
                  #!/bin/bash
                  for i in `seq 10 40`;
                  do
                  echo -n $i “: “
                   curl -s http://mdsec.net/app/ShowPage.ashx?PageNo==$i | grep -Po
                   “<title>(.*)</title>” | sed ‘s/.......\(.*\)......../\1/’
                  done

                  TRY IT!

                            http://mdsec.net/app/

                Netcat

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-78
- cve: ['CVE-2019-0232']
- severity: critical
- quality_score: 13

## Scenario

What does CVE-2019-0232 (Apache Tomcat `CGIServlet` enableCmdLineArguments - Remote Code Execution) involve?

## Analysis / Response

Apache Tomcat `CGIServlet` enableCmdLineArguments is affected by CVE-2019-0232, a remote code execution flaw.

When running on Windows with enableCmdLineArguments enabled, the CGI Servlet in Apache Tomcat 9.0.0.M1 to 9.0.17, 8.5.0 to 8.5.39 and 7.0.0 to 7.0.93 is vulnerable to Remote Code Execution due to a bug in the way the JRE passes command line arguments to Windows. The CGI Servlet is disabled by default. The CGI option enableCmdLineArguments is disable by default in Tomcat 9.0.x (and will be disabled by default in all versions in response to this vulnerability). For a detailed explanation of the JRE behaviour, see Markus Wulftange's blog (https://codewhitesec.blogspot.com/2016/02/java-and-command-line-injections-in-windows.html) and this archived MSDN blog (https://web.archive.org/web/20161228144344/https://blogs.msdn.microsoft.com/twistylittlepassagesallalike/2011/04/23/everyone-quotes-command-line-arguments-the-wrong-way/). It maps to CWE-78.

Root cause: Apache Tomcat `CGIServlet` enableCmdLineArguments executes input as code or OS commands without strict validation.

Scored 8.1 under CVSS v3, CVE-2019-0232 sits in the high band.

Impact: Attackers can execute arbitrary system commands on Windows systems when CGI Servlet is enabled with enableCmdLineArguments, leading to complete server compromise.

**Remediation:** Avoid calling OS commands with user input. Use language-native APIs instead of shell commands. If commands are necessary, use strict allowlists for permitted values. Never concatenate user input into command strings. Implement sandboxing.

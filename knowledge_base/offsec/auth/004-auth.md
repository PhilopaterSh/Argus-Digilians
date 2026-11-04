# AUTH — h1

- source: h1
- class: auth
- cwe: CWE-129
- cve: ['CVE-2020-3187']
- severity: critical
- program: deptofdefense
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** https://██████ vulnerable to CVE-2020-3187 - Unauthenticated arbitrary file deletion in Cisco ASA/FTD

**Vulnerability Description:**
Hi team , while testing i found a host ip https://█████████ which belong to DoD (██████████.mil) running web services interface of Cisco ASA/FTD and it is vulnerable to CVE-2020-3187 - Unauthenticated arbitrary file deletion in Cisco ASA/FTD. An attacker could exploit this vulnerability by sending a crafted HTTP request containing directory traversal character sequences. An exploit could allow the attacker to view or delete arbitrary files on the targeted system. When the device is reloaded after exploitation of this vulnerability, any files that were deleted are restored. The attacker can only view and delete files within the web services file system.

Vulnerable IP : https://█████████
i did a whois search on it and it confirmed it belongs to DoD as you seen below

████

Steps to Reproduce
-----------------------------
go to https://████

█████

you will be redirected to SSL VPN service and you will see a web services interface of Cisco ASA/FTD. In above pic you can see the page we are looking at a web service which is vulnerable to CVE 2020-3187 and you can also see the certificate which indicates that this belongs to █████.mil.

Proof of Concept
-------------------------
Now we know that in CVE-2020-3187 - Unauthenticated arbitrary file deletion in Cisco ASA/FTD. This allow the attacker to view or delete arbitrary files on the targeted system
In this we can delete the files. For example the logo file present on the server at https://████/+CSCOU+/csco_logo.gif can be deleted by the following steps

This can be done by sending a curl request as : curl -H "Cookie: [REDACTED_COOKIE] https://target/+CSCOE+/session_password.html

1. To delete this just hit the following command on your terminals.
```
curl -H “Cookie: [REDACTED_COOKIE] https://█████/+CSCOE+/session_password.html
```
If that did not work because sometimes logo.gif/png has permission issues so try this "https://██████/+CSCOE+/blank.html"

2. You can also delete the file "/+CSCOE+/blank.html" (an empty HTML file), as it might be a problem with the permission of the custom logo file sometimes logo.gif has permission issue so we might not be able to delete but we can delete other files

After, this the files ( logo and blank html page ) will be deleted from the server, for better demonstration check out this video :

- https://video.twimg.com/ext_tw_video/[REDACTED_PHONE]/pu/vid/1270x720/8tccA2VgHV9TDtW4.mp4

Warning : This can lead to a denial of service (DOS) on the VPN by deleting the lua source code files from the file system, which will break the WebVPN interface until the device is rebooted.

Now i haven't deleted the logo file because i didn't wanted to cause any damage so i used another method which can help us confirming that target is vulner

## Analysis / Response

**Vulnerability Class:** auth
**CWE:** CWE-129
**Weakness:** Array Index Underflow
**Severity:** critical
**Endpoint Pattern:** https://█████████

**Impact Assessment:**
High - This vulnerability allows the attacker to delete files within the web services file system.

**Remediation:**
Implement multi-factor authentication. Use secure session management. Apply account lockout policies. Never expose authentication logic client-side.

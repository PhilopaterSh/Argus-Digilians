# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-602
- severity: medium
- program: linkedin
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Information disclosure by sending a GIF
**Affected Asset:** www.linkedin.com

**Vulnerability Description:**
# Summary
- The attacker can view the Operating System, Version Of  The Operating System, Browser, IP Address, Device ID, Phone Model, Time Zone and other critical information about any LinkedIn user they have identified as a victim.

# Steps to Reproduce

1- Create a standard linkedin user account to use in the attack.
2- Select a GIF from the GIF Keyboard and capture the request with Burp Suite while sending it to your victim.
3- Forward all requests until you get to the voyager/api/voyagerMessagingDashMessengerMessages?action=createMessage endpoint. In this request, type the Burp Suite Collaborator url in message.renderContentUnions.externalMedia.media.url in the JSON Data containing (parameters) section.
4- When the victim opens the message box, the attacker will get critical information about the victim.

** Steps Photo **

{F2073194}
{F2073195}
{F2073196}
{F2073197}
{F2073200}
{F2073201}
{F2073202}

## Notes ##

- This vulnerability affects not only smartphones but all platforms where you can use the link (Smart Phones, iPads, Web Browser, Smart TV etc.)
- When the victim uses an apple phone, much more and critical data can be obtained than the android and web version.

{F2073291}
--------
{F2073293}

## PoC Video
{F2073296}
{F2073297}

## References
- Same Attack Scenarios

https://ph-hitachi.medium.com/facebook-bug-poc-external-service-interaction-dns-http-ab55bfdb98f6

## Impact

Black Hat Hackers can get critical information about all LinkedIn users. The information obtained is very important for the privacy of the users and includes information such as IP address, OS versions.

**Steps to Reproduce:**
1- Create a standard linkedin user account to use in the attack.
2- Select a GIF from the GIF Keyboard and capture the request with Burp Suite while sending it to your victim.
3- Forward all requests until you get to the voyager/api/voyagerMessagingDashMessengerMessages?action=createMessage endpoint. In this request, type the Burp Suite Collaborator url in message.renderContentUnions.externalMedia.media.url in the JSON Data containing (parameters) section.
4- When the victim opens the message box, the attacker will get critical information about the victim.

** Steps Photo **

{F2073194}
{F2073195}
{F2073196}
{F2073197}
{F2073200}
{F2073201}
{F2073202}

## Notes ##

- This vulnerability affects not only smartphones but all platforms where you can use the link (Smart Phones, iPads, Web Browser, Smart TV etc.)
- When the victim uses an apple phone, much more and critical data can be obtained than the android and web version.

{F2073291}
--------
{F2073293}

## PoC Video
{F2073296}
{F2073297}

## References
- Same Attack Scenarios

https://ph-hitachi.medium.com/facebook-bug-poc-external-service-interaction-dns-http-ab55bfdb98f6

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-602
**Weakness:** Client-Side Enforcement of Server-Side Security
**Severity:** medium
**Endpoint Pattern:** https://ph-hitachi.medium.com/facebook-bug-poc-external-service-interaction-dns-http-ab55bfdb98f6

**Impact Assessment:**
Black Hat Hackers can get critical information about all LinkedIn users. The information obtained is very important for the privacy of the users and includes information such as IP address, OS versions.

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.

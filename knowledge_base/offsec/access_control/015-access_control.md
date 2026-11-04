# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-284
- severity: critical
- program: deptofdefense
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Subdomain takeover ████████.mil

**Vulnerability Description:**
**Description:**

The subdomain `█████.mil` is pointing to `peosol-lg.███████.`, the domain `██████` is currently available for registration as can be seen at https://www.godaddy.com/nl-nl/domainsearch/find?domainToCheck=█████

Given the rules, residency of the US, of the `us`-tld I decided not to register the domain, also I do believe the output to be enough.

## References

## Impact

Using this vulnerability an attacker can:
- host unwanted/malicious content under your domain
- receive email on subdomains mentioned above
- effectively execute cross-site scripting attacks
- in some cases, steal cookie data
- in some cases, trick password managers into filling passwords

## System Host(s)
██████████.mil

## Affected Product(s) and Version(s)


## CVE Numbers


## Steps to Reproduce
See the DIG output:

```
√ martinvw@denali:~/src > dig █████.mil

; <<>> DiG 9.10.6 <<>> ████.mil
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 44977
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 1, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 512
;; QUESTION SECTION:
;█████████.mil.			IN	A

;; ANSWER SECTION:
██████████.mil.		3600	IN	CNAME	peosol-lg.███.

;; AUTHORITY SECTION:
us.			900	IN	SOA	a.cctld.us. admin.tldns.godaddy. [REDACTED_PHONE]

;; Query time: 166 msec
;; SERVER: 8.8.8.8#[REDACTED_PHONE])
;; WHEN: Fri May 10 15:06:32 CEST 2024
;; MSG SIZE  rcvd: 148
```

And the GoDaddy page: https://www.godaddy.com/nl-nl/domainsearch/find?domainToCheck=███

And whois:

```
√ martinvw@denali:~/src > whois ████████.
% IANA WHOIS server
% for more information on IANA, visit http://www.iana.org
% This query returned 1 object

refer:        whois.nic.us

domain:       US

organisation: Registry Services, LLC
address:      100 S. Mill Ave, Suite 1600
address:      Tempe AZ 85281
address:      United States of America (the)

contact:      administrative
name:         IANA Contact
organisation: Registry Services, LLC
address:      100 S. Mill Ave, Suite 1600
address:      Tempe AZ 85281
address:      United States of America (the)
phone:        [REDACTED_PHONE]
fax-no:       [REDACTED_PHONE]
e-mail:       [REDACTED_EMAIL]

contact:      technical
name:         IANA Contact
organisation: Registry Services, LLC
address:      100 S. Mill Ave, Suite 1600
address:      Tempe AZ 85281
address:      United States of America (the)
phone:        [REDACTED_PHONE]
fax-no:       [REDACTED_PHONE]
e-mail:       [REDACTED_EMAIL]

nserver:      B.CCTLD.US [REDACTED_PHONE]:502:ad09:0:0:0:0:29
nserver:      F.CCTLD.US 2001:500:3682:0:0:0:0:[REDACTED_PHONE]
nserver:      K.CCTLD.US [REDACTED_PHONE]:503:e239:0:0:0:3:1
nserver:      W.CCTLD.US 2001:dcd:1:0:0:0:0:[REDACTED_PHONE]
nserver:      X.CCTLD.US 2001:dcd:2:0:0:0:0:[REDACTED_PHONE]
nserver:     

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-284
**Weakness:** Improper Access Control - Generic
**Severity:** critical
**Endpoint Pattern:** https://www.godaddy.com/nl-nl/domainsearch/find?domainToCheck=█████

**Impact Assessment:**
Using this vulnerability an attacker can:
- host unwanted/malicious content under your domain
- receive email on subdomains mentioned above
- effectively execute cross-site scripting attacks
- in some cases, steal cookie data
- in some cases, trick password managers into filling passwords

## System Host(s)
██████████.mil

## Affected Product(s) and Version(s)


## CVE Numbers

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.

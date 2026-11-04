# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-93
- severity: medium
- program: nextcloud
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** SMTP Command Injection in Appointment Emails via Newlines
**Affected Asset:** nextcloud/calendar

**Vulnerability Description:**
## Summary:
Users can create appointment calendars for other users to book slots on their calendar. When booking a slot, the following request is made:

```
POST /apps/calendar/appointment/1/book HTTP/2
Host: [REDACTED_PHONE]

{"start":[REDACTED_PHONE],"end":"[REDACTED_PHONE]","displayName":"Test User","email":"<BOOKING USER'S EMAIL>","description":"Please accept!\r\n","timeZone":"[REDACTED_TOKEN]"}
```

Next, a confirmation email with a confirmation link is sent to the user who booked the slot via `/var/www/nextcloud/apps/calendar/lib/Service/Appointments/BookingService.php` using the SMTP connection.

The SMTP connection involves the following messages:

```
EHLO nextcloud40gb
250-smtp.gmail.com at your service, [[REDACTED_PHONE]]
250-SIZE 35882577
250-8BITMIME
250-STARTTLS
250-ENHANCEDSTATUSCODES
250-PIPELINING
250-CHUNKING
250 SMTPUTF8
STARTTLS
220 2.0.0 Ready to start TLS
EHLO nextcloud40gb
250-smtp.gmail.com at your service, [[REDACTED_PHONE]]
250-SIZE 35882577
250-8BITMIME
250-AUTH LOGIN PLAIN XOAUTH2 PLAIN-CLIENTTOKEN OAUTHBEARER XOAUTH
250-ENHANCEDSTATUSCODES
250-PIPELINING
250-CHUNKING
250 SMTPUTF8
AUTH LOGIN
334 VXNlcm5hbWU6
aGFja2Vyb25ldGVzdDEyMzRAZ21haWwuY29t
334 UGFzc3dvcmQ6
ZHZob3Z1a3h0aWJrd2JhYg==
235 2.7.0 Accepted
MAIL FROM:<[REDACTED_EMAIL]>
RCPT TO:<BOOKING USER'S EMAIL>
DATA
250 2.1.0 OK u10-20020a056a00124a00b004f783abfa0esm10187854pfi.28 - gsmtp
250 2.1.5 OK u10-20020a056a00124a00b004f783abfa0esm10187854pfi.28 - gsmtp
354  Go ahead u10-20020a056a00124a00b004f783abfa0esm10187854pfi.28 - gsmtp

.
250 2.0.0 OK  [REDACTED_PHONE] u10-20020a056a00124a00b004f783abfa0esm10187854pfi.28 - gsmtp
QUIT
221 2.0.0 closing connection u10-20020a056a00124a00b004f783abfa0esm10187854pfi.28 - gsmtp
```

Unfortunately, as newlines and special characters are not sanitized in the `email` value in the JSON request, a malicious attacker can inject newlines to break out of the `RCPT TO:<BOOKING USER'S EMAIL>` SMTP command and begin injecting arbitrary SMTP commands. Using several properties of the email RFC, an attacker can craft a payload that passes both the PHP validation of the email and the SwiftMail injection. These commands vary depending on the backend email server (Gmail, Outlook, local SMTP server) and thus can have different impacts, such as changing the `MAIL FROM` user, running sensitive commands like `QUEU` to view the current view, and so on. The errors in SMTP are returned in the response, thus making this a non-blind injection.

For example, an attacker can inject a simple `EHLO a` command to view information about the backend server:

```
{"start":[REDACTED_PHONE],"end":"[REDACTED_PHONE]","displayName":"Test User\r\n","email":"\">\r\nEHLO a\r\nRCPT TO:<[REDACTED_EMAIL]>\"@b.com","description":"Please

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-93
**Weakness:** CRLF Injection
**Severity:** medium
**Endpoint Pattern:** POST /apps/calendar/appointment/1/book

**Impact Assessment:**
The impact varies based on which commands are supported by the backend SMTP server. However, the main risk here is that the attacker can then hijack an already-authenticated SMTP session and run arbitrary SMTP commands as the email user, such as sending emails to other users, changing the FROM user, and so on.

https://github.com/nextcloud/security-advisories/security/advisories/GHSA-8xv5-4855-24qf

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.

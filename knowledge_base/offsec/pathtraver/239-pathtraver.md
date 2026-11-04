# PATHTRAVER — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: pathtraver
- cwe: CWE-98

## Scenario

How do I test for and exploit File Inclusion using the LFI to RCE via iconv technique? Give me the payloads.

## Analysis / Response

**LFI to RCE via iconv** — this technique applies to File Inclusion. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Use the iconv wrapper to trigger an OOB in the glibc (CVE-2024-2961), then use your LFI to read the memory regions from `/proc/self/maps` and to download the glibc binary. Finally you get the RCE by exploiting the `zend_mm_heap` structure to call a `free()` that have been remapped to `system` using `custom_heap._free`.

**Requirements**:

- PHP 7.0.0 (2015) to 8.3.7 (2024)
- GNU C Library (`glibc`) <=  2.39
- Access to `convert.iconv`, `zlib.inflate`, `dechunk` filters

**Exploit**:

- [ambionics/cnext-exploits](https://github.com/ambionics/cnext-exploits/tree/main)

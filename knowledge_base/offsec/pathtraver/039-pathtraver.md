# PATHTRAVER — qwen_cve

- source: qwen_cve
- class: pathtraver
- cwe: CWE-22
- cve: ['CVE-2009-1558']
- severity: high
- quality_score: 11

## Scenario

Which vulnerability class best describes CVE-2009-1558 (Cisco Linksys WVC54GCA 1.00R22/1.00R24 - Local File Inclusion)?
A) path traversal
B) memory corruption
C) CRLF injection
D) information disclosure

## Analysis / Response

Answer: A) path traversal.

Why: Directory traversal vulnerability in adm/file.cgi on the Cisco Linksys WVC54GCA wireless video camera with firmware 1.00R22 and 1.00R24 allows remote attackers to read arbitrary files via a %2e. (encoded dot dot) or an absolute pathname in the next_file parameter. CVE-2009-1558 is recorded as CWE-22.

**Remediation:** Canonicalize and validate all file paths. Use a chroot jail or sandboxed directory. Implement path allowlists. Strip or reject sequences like ../ and null bytes. Use framework-provided secure file access APIs.

# PATHTRAVER — qwen_cve

- source: qwen_cve
- class: pathtraver
- cwe: CWE-22
- cve: ['CVE-2008-6668']
- severity: high
- quality_score: 11

## Scenario

True or false: CVE-2008-6668 is mapped to CWE-22.

## Analysis / Response

True. CVE-2008-6668 (nweb2fax <=0.2.7 - Local File Inclusion) is recorded with CWE-22, consistent with its classification as path traversal.

Multiple directory traversal vulnerabilities in nweb2fax 0.2.7 and earlier allow remote attackers to read arbitrary files via a .. (dot dot) in the (1) id parameter to comm.php and (2) var_filename parameter to viewrq.php.

**Remediation:** Canonicalize and validate all file paths. Use a chroot jail or sandboxed directory. Implement path allowlists. Strip or reject sequences like ../ and null bytes. Use framework-provided secure file access APIs.

# PATHTRAVER — qwen_cve

- source: qwen_cve
- class: pathtraver
- cwe: CWE-22
- severity: high
- quality_score: 9

## Scenario

How are path traversal (directory traversal) fixes commonly bypassed?

## Analysis / Response

Watch for these pitfalls when fixing path traversal (directory traversal).

Stripping `../` once is defeated by `....//`, and checking before URL decoding is defeated by encoded sequences. Prefix checks with plain string comparison can be fooled by sibling directories such as `/var/www/files_backup` matching `/var/www/files`; compare resolved paths with a trailing separator. Windows accepts both slash types and drive letters, which Linux-oriented filters miss.

Key points (path traversal):
- Canonicalize first, then compare against the allowed base directory.
- Indirect references such as file IDs remove user control over paths entirely.
- Read access to configuration files often leads to credential compromise.

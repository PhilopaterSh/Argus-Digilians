# PATHTRAVER — qwen_cve

- source: qwen_cve
- class: pathtraver
- cwe: CWE-22
- cve: ['CVE-2013-1891']
- severity: high
- quality_score: 10

## Scenario

Give a technical description of CVE-2013-1891.

## Analysis / Response

CVE-2013-1891 describes a Path Traversal flaw. NVD describes CVE-2013-1891 as follows: In OpenCart 1.4.7 to 1.5.5.1, implemented anti-traversal code in filemanager.php is ineffective and can be bypassed. A traversal bug exists when the application trusts the path it receives and does not verify the resolved location. The weakness recorded for CVE-2013-1891 is CWE-22.

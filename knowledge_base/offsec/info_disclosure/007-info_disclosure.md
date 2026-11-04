# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2020-9480']
- severity: medium
- quality_score: 11

## Scenario

We can't patch Apache Spark today. How do we reduce exposure to CVE-2020-9480?

## Analysis / Response

Fixing CVE-2020-9480 in Apache Spark:

1) Patch: The fix ships in Apache Spark 2.4.5; move every instance to that release or newer.

2) Until Apache Spark is patched: Enforce authentication centrally in Apache Spark (middleware or filter) rather than per-endpoint. Restrict network access to the Apache Spark administrative interface.

3) References: https://lists.apache.org/thread.html/ra0e62a18ad080c4ce6df5e0202a27eaada75222761efc3f7238b5a3b%40%3Ccommits.doris.apache.org%3E, https://lists.apache.org/thread.html/rb3956440747e41940d552d377d50b144b60085e7ff727adb0e575d8d%40%3Ccommits.submarine.apache.org%3E, https://spark.apache.org/security.html#CVE-2020-9480, https://www.oracle.com/security-alerts/cpuApr2021.html

4) Verify by re-running the CVE-2020-9480 check on POST /v1/submissions/create; the indicators should be gone.

# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-306
- cve: ['CVE-2020-13927']
- severity: critical
- quality_score: 13

## Scenario

What is CVE-2020-13927?

## Analysis / Response

CVE-2020-13927 is an authentication bypass vulnerability in Airflow Experimental.

The previous default setting for Airflow's Experimental API was to allow all API requests without authentication, but this poses security risks to users who miss this fact. From Airflow 1.10.11 the default has been changed to deny all requests by default and is documented at https://airflow.apache.org/docs/1.10.11/security.html#api-authentication. Note this change fixes it for new installs but existing users need to change their config to default `[api]auth_backend = airflow.api.auth.backend.deny_all` as mentioned in the Updating Guide: https://github.com/apache/airflow/blob/1.10.11/UPDATING.md#experimental-api-will-deny-all-request-by-default It maps to CWE-306 and CWE-1188 and CWE-1056.

Root cause: Airflow Experimental performs authentication checks inconsistently, leaving at least one path unprotected.

Scored 9.8 under CVSS v3, CVE-2020-13927 sits in the critical band.

Impact: Allows unauthorized access to Airflow Experimental REST API

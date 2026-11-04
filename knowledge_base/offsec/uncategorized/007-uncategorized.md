# UNCATEGORIZED — Official CVE Program record (CVEProject/cvelistV5)

- source: Official CVE Program record (CVEProject/cvelistV5)
- class: uncategorized
- cve: ['CVE-2001-1473']

## Scenario

Give me a source-grounded overview of CVE-2001-1473.

## Analysis / Response

CVE-2001-1473: The SSH-1 protocol allows remote servers to conduct man-in-the-middle attacks and replay a client challenge response to a target server by creating a Session ID that matches the Session ID of the target, but which uses a public key pair that is weaker than the target's public key, which allows the attacker to compute the corresponding private key and use the target's Session ID with the compromised key pair to masquerade as the target.

Source: https://www.cve.org/CVERecord?id=CVE-2001-1473

# PATHTRAVER — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: pathtraver
- cwe: CWE-98

## Scenario

I'm doing an authorized pentest and need the Linux version approach for File Inclusion. Walk me through it with payloads.

## Analysis / Response

**Linux version** — this technique applies to File Inclusion. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Extract `/etc/shadow` files.

```powershell
http://example.com/index.php?page=../../../../../../etc/shadow
```

Then crack the hashes inside in order to login via SSH on the machine.

Another way to gain SSH access to a Linux machine through LFI is by reading the private SSH key file: `id_rsa`.
If SSH is active, check which user is being used in the machine by including the content of `/etc/passwd` and try to access `/<HOME>/.ssh/id_rsa` for every user with a home.

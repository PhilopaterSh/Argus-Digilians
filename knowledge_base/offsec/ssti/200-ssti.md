# SSTI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssti
- cwe: CWE-311

## Scenario

Walk me through Web Security for Developers — How the Internet Works: Encryption with practical steps from the source material.

## Analysis / Response

Based on Web Security for Developers (Encryption):

Encryption
                 When the web was first invented, HTTP requests and responses were sent in
                 plaintext form, which meant they could be read by anyone intercepting the
                 data packets; this kind of interception is known as a man-in-the-middle attack.
                 Because private communication and online transactions are common on
                 the modern web, web servers and browsers protect their users from such
                 attacks by using encryption, a method of disguising the contents of messages
                 from prying eyes by encoding them during transmission.
                      To secure their communications, web servers and browsers send requests
                 and responses by using Transport Layer Security (TLS), a method of encryp-
                 tion that provides both privacy and data integrity. TLS ensures that packets
                 intercepted by a third party can’t be decrypted without the appropriate
                 encryption keys. It also ensures that any attempt to tamper with the packets
                 will be detectable, which ensures data integrity.

Use only on systems you are authorized to test; capture evidence and include remediation.

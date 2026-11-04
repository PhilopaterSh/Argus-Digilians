# SSTI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssti
- cwe: CWE-311

## Scenario

Describe methodology and key techniques for Web Security for Developers — Encryption: Obtaining a Digital Certificate during an authorized assessment.

## Analysis / Response

Based on Web Security for Developers (Obtaining a Digital Certificate):

Obtaining a Digital Certificate
Obtaining a digital certificate for your website from a certificate author-
ity requires a few steps, by which the authority verifies that you own your
domain. The precise way you perform these steps differs depending on
which certificate authority you choose.
     The first step is to generate a key pair, a small digital file containing ran-
domly generated public and private encryption keys. Next, you use this key
pair to generate a certificate signing request (CSR) that contains the public key
and domain name of your website, and upload the request to a certificate
authority. Before honoring the signing request and issuing the certificate,
the certificate authority will require you to demonstrate to them that you
have control of the internet domain contained in the CSR. Once domain
ownership has been verified, you can download the certificate and install it
on your web server along with the key pair.

Use only on systems you are authorized to test; capture evidence and include remediation.

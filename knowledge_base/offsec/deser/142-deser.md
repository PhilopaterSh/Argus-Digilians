# DESER — portswigger_labs_sft

- source: portswigger_labs_sft
- class: deser
- cwe: CWE-502

## Scenario

Help me complete the lab "Exploiting Ruby deserialization using a documented gadget chain" from PortSwigger Web Security Academy. Category: Insecure deserialization. Difficulty: Practitioner.

This lab uses a serialization-based session mechanism and the Ruby on Rails framework. There are documented exploits that enable remote code execution via a gadget chain in this framework.

To solve the lab, find a documented exploit and adapt it to create a malicious serialized object containing a remote code execution payload. Then, pass this object into the website to delete the `morale.txt` file from Carlos's home directory.

You can log in to your own account using the following credentials: wiener:peter

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Insecure deserialization: "Exploiting Ruby deserialization using a documented gadget chain".

## Solution steps

1. Log in to your own account and notice that the session cookie contains a serialized ("marshaled") Ruby object. Send a request containing this session cookie to Burp Repeater.
2. Browse the web to find the `Universal Deserialisation Gadget for Ruby 2.x-3.x` by `vakzz` on `devcraft.io`. Copy the final script for generating the payload.
3. Modify the script as follows: Change the command that should be executed from `id` to `rm /home/carlos/morale.txt`. Replace the final two lines with `puts Base64.encode64(payload)`. This ensures that the payload is output in the correct format for you to use for the lab.
4. Run the script and copy the resulting Base64-encoded object.
5. In Burp Repeater, replace your session cookie with the malicious one that you just created, then URL encode it.
6. Send the request to solve the lab.

## Vulnerability note

Underlying issue: Insecure deserialization (CWE-502). Avoid deserializing untrusted data; use allowlists, signing, and safer formats like JSON with schema validation.

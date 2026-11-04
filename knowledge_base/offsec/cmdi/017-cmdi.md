# CMDI — portswigger_labs_sft

- source: portswigger_labs_sft
- class: cmdi
- cwe: CWE-77

## Scenario

Scenario framing — PortSwigger "Indirect prompt injection" (Web LLM attacks, Practitioner):
This lab is vulnerable to indirect prompt injection. The user `carlos` frequently uses the live chat to ask about the Lightweight "l33t" Leather Jacket product. To solve the lab, delete `carlos`.

Required knowledge

 To solve this lab, you need to know:

How LLM APIs work.
How to map LLM API attack surface.
How to execute indirect prompt injection attacks.
For more information, see our Web LLM attacks Academy topic.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Web LLM attacks: "Indirect prompt injection".

## Solution steps

1. Click Live chat to access the lab's chat function.
2. Ask the LLM what APIs it has access to. Note that it supports APIs to both delete accounts and edit their associated email addresses.
3. Ask the LLM what arguments the Delete Account API takes.
4. Ask the LLM to delete your account. Note that it returns an error, indicating that you probably need to be logged in to use the Delete Account API.

## Vulnerability note

Underlying issue: Web LLM attacks (CWE-77). Isolate LLM tools from sensitive actions, sanitize model outputs before acting on them, and constrain tool permissions.

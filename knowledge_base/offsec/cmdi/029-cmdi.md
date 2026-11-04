# CMDI — portswigger_labs_sft

- source: portswigger_labs_sft
- class: cmdi
- cwe: CWE-77

## Scenario

I'm stuck on the PortSwigger lab "Exploiting AI agents to trigger secondary vulnerabilities" (Practitioner, Web LLM attacks). Here's the scenario:

This lab is vulnerable to indirect prompt injection. The application features an AI-powered scanner that can be manipulated into exploiting a routing-based SSRF vulnerability on the internal network.

You can log in to your own account using the following credentials: `wiener:peter`.

To solve the lab, delete `carlos`.

Note

 This lab uses a live LLM, which can be unpredictable. If the LLM does not respond as expected, you may need to rephrase your prompts or repeat the scanning process.

Required knowledge

 To solve this lab, you need to know:

How indirect prompt injection can be used to manipulate an LLM's behavior via third-party content.
How routing-based SSRF can be triggered by manipulating the `Host` header.
For more information, see our AI-powered scanner vulnerabilities topic.

Labs in this sub-topic collect telemetry data, including AI interaction logs. For details on what data they collect and how we use it, see our Academy Lab Telemetry Privacy Notice.

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Web LLM attacks: "Exploiting AI agents to trigger secondary vulnerabilities".

No official step-by-step solution text was available on the lab page at scrape time. Review the lab description carefully, reproduce the issue in your own authorized lab instance, and consult the PortSwigger topic guide for Web LLM attacks.

## Vulnerability note

Underlying issue: Web LLM attacks (CWE-77). Isolate LLM tools from sensitive actions, sanitize model outputs before acting on them, and constrain tool permissions.

# DESER — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: deser
- cwe: CWE-502

## Scenario

Give me a rundown of ViewState for Insecure Deserialization: when to use it and the payloads involved.

## Analysis / Response

**ViewState** — this technique applies to Insecure Deserialization. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

In Java, ViewState refers to the mechanism used by frameworks like JavaServer Faces (JSF) to maintain the state of UI components between HTTP requests in web applications. There are 2 major implementations:

* Oracle Mojarra (JSF reference implementation)
* Apache MyFaces

**Tools**:

* [joaomatosf/jexboss](https://github.com/joaomatosf/jexboss) - JexBoss: Jboss (and Java Deserialization Vulnerabilities) verify and EXploitation Tool
* [Synacktiv-contrib/inyourface](https://github.com/Synacktiv-contrib/inyourface) - InYourFace is a software used to patch unencrypted and unsigned JSF ViewStates.

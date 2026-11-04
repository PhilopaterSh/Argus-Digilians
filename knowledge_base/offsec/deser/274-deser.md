# DESER — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: deser
- cwe: CWE-502

## Scenario

How do I test for and exploit Insecure Deserialization using the POP Gadgets technique? Give me the payloads.

## Analysis / Response

**POP Gadgets** — this technique applies to Insecure Deserialization. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

> A POP (Property Oriented Programming) gadget is a piece of code implemented by an application's class, that can be called during the deserialization process.

POP gadgets characteristics:

* Can be serialized
* Has public/accessible properties
* Implements specific vulnerable methods
* Has access to other "callable" classes

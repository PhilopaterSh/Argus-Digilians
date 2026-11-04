# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe methodology and key techniques for From Day Zero to Zero Day — Mapping Code to Attack Surface: For example, Microsoft Excel handles not only Excel workbook file for- during an authorized assessment.

## Analysis / Response

Based on From Day Zero to Zero Day (web-relevant) (For example, Microsoft Excel handles not only Excel workbook file for-):

For example, Microsoft Excel handles not only Excel workbook file for-
                 mats (.xls, .xlsx) but also Symbolic Link (.slk), dBase (.dbf ), Data Interchange
                 Format (.dif ), and more. And these are just file input vectors; you also have
                 to worry about inter-process communication (IPC) and other network vectors.
                 For example, another process may control Excel via Component Object
                 Model (COM) interfaces, or it may fetch data from the internet via external
                 data connections. All are potential sources for exploitable vulnerabilities.
                      The large attack surfaces of modern software can be overwhelming.
                 Less experienced vulnerability researchers may try to test every possible
                 source, falling into numerous rabbit holes and wasting effort. While this tac-
                 tic makes sense in a black-box scenario in which the researcher is limited to
                 what they can enumerate of a target’s external attack surface, code review
                 offers more efficient means to narrow down this search. For example, when
                 researching a web application, instead of laboriously brute-forcing routes
                 while attempting to dodge rate limits and web application firewalls, you can
                 simply check the relevant routing code.

Use only on systems you are authorized to test; capture evidence and include remediation.

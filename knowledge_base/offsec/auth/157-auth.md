# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: From Day Zero to Zero Day — Mapping Code to Attack Surface: Web frameworks create opportunities to refactor code, such as moving

## Analysis / Response

Based on From Day Zero to Zero Day (web-relevant) (Web frameworks create opportunities to refactor code, such as moving):

Web frameworks create opportunities to refactor code, such as moving
                  nested routes under /items to another file. This makes the code easier to
                  read both for developers and for you, the aspiring vulnerability researcher.

                  The Model–View–Controller Architecture
                  One common pattern among web frameworks is the model–view–controller
                  (MVC) architecture, which separates the code into three main groups. Famil-
                  iarity with this pattern will help you quickly analyze frameworks, understand
                  the flow of data through sources and sinks, and focus on the critical business
                  logic that is most likely to contain vulnerabilities instead of getting caught up
                  in irrelevant code. The MVC architecture comprises three parts:

                       Model    Handles the “business logic,” such as data structures
                       View Handles the user interface, such as layouts and templates
                       Controller Handles the control flow from requests to relevant model
                       and view components

                       The routing code tends to appear around the controller components.

Use only on systems you are authorized to test; capture evidence and include remediation.

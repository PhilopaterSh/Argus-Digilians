# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Web Application Hacker's Handbook 2e — Proxy, you can use the Paste from File context menu option to achieve

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Proxy, you can use the Paste from File context menu option to achieve):

Proxy, you can use the Paste from File context menu option to achieve
                      this. This approach usually is the easiest and least likely to run into the
                      problems described previously.

               Recompiling and Executing Outside the Browser
               In some cases, it is not necessary to modify the component’s behavior while it
               is being executed. For example, some browser extension components validate
               user-supplied input and then obfuscate or encrypt the result before sending
               it to the server. In this situation, you may be able to modify the component to
               perform the required obfuscation or encryption on arbitrary unvalidated input
               and simply output the result locally. You can then use your proxy to intercept the
               relevant request when the original component submits the validated input, and
               you can replace this with the value that was output by your modiﬁed component.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

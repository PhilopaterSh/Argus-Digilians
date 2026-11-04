# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

I'm preparing a bug bounty test plan covering Web Application Hacker's Handbook 2e — 6.3.3 Decompile all compiled clients that are present, and extract any refer-. What does the source recommend?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (6.3.3 Decompile all compiled clients that are present, and extract any refer-):

6.3.3 Decompile all compiled clients that are present, and extract any refer-
                     ences to server-side functionality.
               6.3.4 Most data that is subject to horizontal access controls is accessed using
                     an identiﬁer, such as an account number or order reference. To test
                     whether access controls are effective using only a single account, you
                     must try to guess or discover the identiﬁers associated with other users’
                     data. If possible, generate a series of identiﬁers in quick succession
                     (for example, by creating several new orders). Attempt to identify any
                     patterns that may enable you to predict the identiﬁers issued to other
                     users. If there is no way to generate new identiﬁers, you are probably
                     restricted to analyzing those you already have and guessing on that
                     basis.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

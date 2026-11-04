# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Walk me through Web Application Hacker's Handbook 2e — The root cause of the vulnerability was that the user-supplied data was with practical steps and examples from the source material.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (The root cause of the vulnerability was that the user-supplied data was):

The root cause of the vulnerability was that the user-supplied data was
                being stored as null-terminated strings within 4096-byte blocks of memory.
                The data was copied in a checked operation, so no straight overﬂow was pos-
                sible. However, if overlong input was submitted, the copy operation resulted
                in the loss of the null terminator, so the string ﬂowed into the next data in
                memory. Therefore, when the application parsed the request parameters, it
                continued up until the next null byte and therefore included the parameters
                supplied by another user.

c16.indd 638                                                                                           8/19/2011 12:16:35 PM

38                                                                         Stuttard c16.indd V2 - 08/16/2011 Page 639

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).

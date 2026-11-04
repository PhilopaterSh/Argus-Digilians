# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What does the Hacking APIs checklist cover for endpoint analysis and authentication testing?

## Analysis / Response

From the API Hacking Checklist:

Endpoint analysis
- Find and review API documentation.
- Reverse engineer the API.
- Analyze responses for information disclosures, excessive data exposures, and business logic flaws.

Authentication testing
- Conduct basic authentication testing.
- Attack and manipulate API tokens.

In practice, endpoint analysis means locating any docs (Swagger/OpenAPI, developer portals), reconstructing undocumented requests by observing the app, and then reading responses carefully - excessive data exposure often leaks identifiers (user IDs, GUIDs, emails) you'll reuse in later authorization attacks, and verbose responses reveal business-logic assumptions worth abusing. Authentication testing covers weak credential handling, flawed login/registration flows, and token attacks: inspecting JWTs for weak signing or the none algorithm, testing token predictability with Burp Sequencer, and replaying or tampering with tokens. Treat this as the bridge between recon and exploitation: the data and tokens you harvest here feed directly into BOLA, BFLA, and mass assignment testing.

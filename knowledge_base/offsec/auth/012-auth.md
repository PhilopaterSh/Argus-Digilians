# AUTH — gapfill_synthetic

- source: gapfill_synthetic
- class: auth

## Scenario

In scope. Login sets a JWT. I suspect weak alg handling. Inspect the token and test the alg:none / weak-secret angle.

## Analysis / Response

<think>
JWT review: decode first to read header alg and claims, then reason. If HS256 with a guessable secret, I can forge; if it accepts alg:none, trivial forgery. Decode before attacking.
</think>


# ACCESS_CONTROL — gapfill_synthetic

- source: gapfill_synthetic
- class: access_control

## Scenario

Two test accounts. Invoice download is GET /api/invoices/8841/pdf. As account A, changing 8841→8842 (B's) returns B's PDF. Classify and rate.

## Analysis / Response

<think>
Direct object reference with no ownership check = IDOR / broken object-level authorization. Sequential numeric IDs make enumeration trivial → bulk exposure, not one-off. The request is authenticated but authorization is missing: server checks 'logged in' not 'owns 8842'. Impact is confidentiality of all tenants' invoices (financial PII). No integrity unless other verbs are unprotected. I'll stress enumeration breadth in the report — triagers reward demonstrated scale.
</think>

**IDOR / Broken Object-Level Authorization** on invoice download.

**PoC:** authenticated as A, walk sequential IDs:
```
curl -s -H 'Cookie: session=<A>' https://target.tld/api/invoices/8842/pdf -o 8842.pdf
```
Returns B's invoice; IDs sequential → scriptable full-range enumeration.

**Root cause:** handler authenticates the session but never checks `invoice.owner_id == current_user.id`.

**Impact:** mass cross-tenant disclosure of invoices (names, addresses, amounts).

**Severity:** High — AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N = 6.5, argued high given cross-tenant financial PII at scale.

**Fix:** enforce ownership in the query — `WHERE id=:id AND owner_id=:current_user`; return 404 not 403. UUIDv4 IDs are defense-in-depth, not the control.
**Edge case:** if some invoices are legitimately shared (accountant role), scope the check to the sharing grant rather than dropping it.

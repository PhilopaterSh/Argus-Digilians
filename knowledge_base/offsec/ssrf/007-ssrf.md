# SSRF — gapfill_synthetic

- source: gapfill_synthetic
- class: ssrf

## Scenario

The avatar feature fetches a user-supplied image URL server-side: GET /profile/avatar?url=https://... and returns the bytes. In scope. Risk, and how do I prove impact beyond 'it fetches URLs'?

## Analysis / Response

<think>
Server-side fetch of an arbitrary URL = SSRF. The real question is impact; hitting my OAST is only informational. To escalate I want internal reach or cloud metadata — on AWS, 169.254.169.254 IMDSv1 leaks credentials, the money shot. Returning bytes gives a read channel (full, not blind). Watch for filters blocking 169.254/private ranges; bypass via alternate IP encodings or a redirect from an allowed host. Severity hinges on internal services; metadata cred theft is critical, S:C.
</think>

**Full-read SSRF** in the avatar `url` parameter.

**PoC — escalate to AWS IMDSv1 credential theft:**
```
/profile/avatar?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/
/profile/avatar?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>
```
Body returns AccessKeyId/SecretAccessKey/Token.

**Root cause:** user URL passed to a server HTTP client with no allowlist, no scheme/host validation, private/link-local ranges not blocked.

**Impact:** IAM role credential theft → cloud account pivot. Critical.

**Severity:** Critical — AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:N ≈ 9.3 (S:C crosses into cloud control plane).

**Fix:** allowlist destination hosts; resolve DNS and reject RFC1918/link-local; disable redirects or re-validate each hop; require IMDSv2.
**Edge case:** if only IMDSv2 is enabled the metadata path 401s — pivot to internal admin ports before downgrading.

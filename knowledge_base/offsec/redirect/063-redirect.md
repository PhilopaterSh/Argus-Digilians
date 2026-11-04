# REDIRECT — h1

- source: h1
- class: redirect
- cwe: CWE-601
- severity: medium
- program: chaturbate
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Open redirect in securegatewayaccess.com / secure.chaturbate.com via prejoin_data parameter
**Affected Asset:** *.securegatewayaccess.com

**Vulnerability Description:**
##Summary##
Hello, I have found that if there is a valid `weg_digest` parameter in the in the GET request to https://secure.chaturbate.com/post and other parameters are invalid, a Location header will be automatically constructor based on the contents of the `prejoin_data` parameter. This allows someone to change the base root and create an open redirect.

Even more, it has been observed that this specific request also works under the https://securegatewayaccess.com domain and an open redirect can also be created from that domain.

PS : Because this affects both URL's and `securegatewayaccess.com` seems to be a critical I have marked this as medium instead of low.

## Steps To Reproduce:
- Call in browser this URL :

```
https://securegatewayaccess.com/post?prejoin_data=domain%2Fevil.com/?=&weg_digest=eacde2b0b10379e9848390da67ed883666fe083a9ad892fae85c590ddd354e8c
```

- Or under the secure.chaturbate domain this URL :

```
https://secure.chaturbate.com/post?prejoin_data=domain%2Fevil.com/?=&weg_digest=eacde2b0b10379e9848390da67ed883666fe083a9ad892fae85c590ddd354e8c
```

- This can also be linked with the /external_link request from the root url to create a chained redirect :

```
https://chaturbate.com/external_link/?url=https%3A%2F%2Fsecure.chaturbate.com%2Fpost%3Fprejoin_data%3Ddomain%252Fevil.com%2F%3F%3D%26weg_digest%3Deacde2b0b10379e9848390da67ed883666fe083a9ad892fae85c590ddd354e8c
```

All requests will have as answer this header :

```
Location: http://evil.com/?=/tipping/purchase_tokens/
```

## Supporting Material/References:
N/A

## Impact

Open redirect that facilitate potential phishing attacks.

**Steps to Reproduce:**
- Call in browser this URL :

```
https://securegatewayaccess.com/post?prejoin_data=domain%2Fevil.com/?=&weg_digest=eacde2b0b10379e9848390da67ed883666fe083a9ad892fae85c590ddd354e8c
```

- Or under the secure.chaturbate domain this URL :

```
https://secure.chaturbate.com/post?prejoin_data=domain%2Fevil.com/?=&weg_digest=eacde2b0b10379e9848390da67ed883666fe083a9ad892fae85c590ddd354e8c
```

- This can also be linked with the /external_link request from the root url to create a chained redirect :

```
https://chaturbate.com/external_link/?url=https%3A%2F%2Fsecure.chaturbate.com%2Fpost%3Fprejoin_data%3Ddomain%252Fevil.com%2F%3F%3D%26weg_digest%3Deacde2b0b10379e9848390da67ed883666fe083a9ad892fae85c590ddd354e8c
```

All requests will have as answer this header :

```
Location: http://evil.com/?=/tipping/purchase_tokens/
```

## Supporting Material/References:
N/A

**Proof of Concept:**
```
https://securegatewayaccess.com/post?prejoin_data=domain%2Fevil.com/?=&weg_digest=eacde2b0b10379e9848390da67ed883666fe083a9ad892fae85c590ddd354e8c
```

```
https:/

## Analysis / Response

**Vulnerability Class:** redirect
**CWE:** CWE-601
**Weakness:** Open Redirect
**Severity:** medium
**Endpoint Pattern:** https://secure.chaturbate.com/post

**Impact Assessment:**
Open redirect that facilitate potential phishing attacks.

**Remediation:**
Validate redirect URLs against an allowlist of permitted domains. Use relative URLs for internal redirects. Never place user input directly in redirect targets.

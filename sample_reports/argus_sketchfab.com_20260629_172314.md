# Argus Security Report
**Target:** sketchfab.com
**Scan Mode:** aggressive
**Generated:** 2026-06-29T17:23:14.436199
**Risk Score:** 9/10

## Summary
- Total Findings: 21
- High: 4
- Medium: 1
- Info: 16

## Knowledge Graph Relationships

(img.email1.sketchfab.com) --[EXPOSES]--> (abuse@sendinblue.com)
(r.email1.sketchfab.com) --[EXPOSES]--> (abuse@sendinblue.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (click.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (landings.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (www.blog.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (img.email2.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (static.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (www.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (api.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (r.email3.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (staging1.blog.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (blog.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (massive.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (staging-enterprise.blog.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (www.staging-enterprise.blog.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (media.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (r.email2.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (www.staging1.blog.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (e6f79c614c67.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (img.email3.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (forum.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (www.staging2.blog.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (staging2.blog.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (help.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (r.email1.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (img.email1.sketchfab.com)
(sketchfab.com) --[HAS_SUBDOMAIN]--> (labs.sketchfab.com)
(sketchfab.com) --[HOSTS]--> (108.159.102.125)

## Findings

### [Info] ports — api.sketchfab.com
- **Summary:** Open ports: 80, 443

### [Info] tech — api.sketchfab.com
- **Summary:** Tech: CloudFront

### [Info] waf — api.sketchfab.com
- **Summary:** WAF: Not detected

### [Info] headers — api.sketchfab.com
- **Summary:** HTTP Headers captured

### [High] secrets — img.email1.sketchfab.com
- **Summary:** Secrets in HTML

### [High] leak — img.email1.sketchfab.com
- **Summary:** Sensitive files found!

### [Info] ports — img.email1.sketchfab.com
- **Summary:** Open ports: 80, 443, 8080, 8443

### [Info] tech — img.email1.sketchfab.com
- **Summary:** Tech: cloudflare

### [Info] waf — img.email1.sketchfab.com
- **Summary:** WAF: Cloudflare

### [Info] headers — img.email1.sketchfab.com
- **Summary:** HTTP Headers captured

### [High] secrets — r.email1.sketchfab.com
- **Summary:** Secrets in HTML

### [High] leak — r.email1.sketchfab.com
- **Summary:** Sensitive files found!

### [Info] ports — r.email1.sketchfab.com
- **Summary:** Open ports: 80, 443

### [Info] tech — r.email1.sketchfab.com
- **Summary:** Tech: cloudflare

### [Info] waf — r.email1.sketchfab.com
- **Summary:** WAF: Cloudflare

### [Info] headers — r.email1.sketchfab.com
- **Summary:** HTTP Headers captured

### [Medium] vulnerability — sketchfab.com
- **Summary:** Nikto finding

### [Info] ports — sketchfab.com
- **Summary:** Open ports: 80, 443

### [Info] tech — sketchfab.com
- **Summary:** Tech: CloudFront

### [Info] waf — sketchfab.com
- **Summary:** WAF: Not detected

### [Info] headers — sketchfab.com
- **Summary:** HTTP Headers captured

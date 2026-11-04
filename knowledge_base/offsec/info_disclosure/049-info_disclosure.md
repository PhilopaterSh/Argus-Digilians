# INFO_DISCLOSURE — h1

- source: h1
- class: info_disclosure
- cwe: CWE-840
- severity: medium
- program: flickr
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** critical server misconfiguration lead to access to any user sensitive data which include user email and password
**Affected Asset:** *.flickr.com

**Vulnerability Description:**
Hi flickr team,
I found a critical issue lead to access to any user sensitive data which include user hashed password and possibly can lead to takeover any user account on  flickr's main site, literally i can get all  user information from database with no restrictions ,
Let me explain how this happen:

As we know Flickr that it was belong to Yahoo and also it was  hosted on many servers, including Amazon servers,
And after Flickr reboot as an independent and separate organization from Yahoo
This servers still has full access to Flickr’s main server databases 
The attacker can use this old flickr server to get a lot of sensitive information belong to any user 
By using “published user image name” and search by it ,on Flickr yahoo old server

For example :
We have user x  and he posted a photo named “golden_arrow_img” 
Now let’s say the attacker know his victim user and now he know how to get all user sensitive data , he will go to misconfigured server  which it’s address is : https://[REDACTED_PHONE] But when he goes to this address, he only sees an error message and the logo of Flickr, and after a while of checking the available paths, I found that when I add the word start, all the content of the server appears,the address will be https://[REDACTED_PHONE]/start , you will see a search box, go to search by the name of the published user image which is for example “golden_arrow_img”, but you will not see the results in The page, server will redirect you to the first error page , the request must be stopped by burp-suite proxy and send it to the repeater then repeat the request, you will see the results, search in the repeater results for the function called ==“Y.listData”==
You will see under this function all user sensitive data, which is will be like :

```
Y.listData = {
		"user": {
				"id": "█████",
				"first_name": "███████",
				"last_name": "████",
				"email": "███",
				"date_creation": "█████",
				"date_modified": "0",
				"password": "██████",
				"city": "los angelos",
				"country": "United states",
				"check_code": "",
				"email_conf": "1",
				"email_conf_bounce": "0",
				"nsid": "███████",
				"character_name": "███████",
				"gender": "M",
				"magic_email": "",
				"is_admin": "0",
				"is_bad": "0",
				"prefs_main_1": "2056",
				"prefs_main_2": "262161",
				"mail_buffer": "",
				"deleted": "0",
				"kill": "0",
				"kill_from": "0",
				"refer_code": "",
				"date_limit": "0",
				"photo_id_limit": "0",
				"date_premium_end": "0",
				"is_paid_pro": "0",
				"has_order_history": "0",
				"gifts_to_give": "0",
				"path_alias": null,
				"date_iconchange": "0",
				"pref_default_license": "0",
				"upload_email_tags": "",
				"upload_ema

## Analysis / Response

**Vulnerability Class:** info_disclosure
**CWE:** CWE-840
**Weakness:** Business Logic Errors
**Severity:** medium
**Endpoint Pattern:** https://34.235.208.201

**Impact Assessment:**
The attacker can access to any user sensitive data which include user hashed password and possibly lead to takeover any flickr user account , literally the attacker can get all  user information from database with no restrictions

**Remediation:**
Remove sensitive data from error messages, headers, and responses. Implement proper access controls. Disable debug modes in production.

# REDIRECT — h1

- source: h1
- class: redirect
- cwe: CWE-601
- severity: low
- program: semrush
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** protocol & Ports are not shown in third-party site redirect warning page 
**Affected Asset:** *.semrush.com

**Vulnerability Description:**
**Summary:** 
protocol & Ports are not shown in third-party site redirect warning page 

**Vulnerable Endpoint :-** https://www.semrush.com/redirect?url=ftp://evil.com:1337

**Description:** 
I noticed #311330 this report where you guys fixed a open redirect report by adding a external third-party site redirect warning page . It was a great fix . Although a issue caught in my eye . Urls contains a **protocol** and **Ports** . If I add a url with any other **protocol** like **ftp://** then it's not shown in the external warning page what can be used to take a user to any other place then user expected to go  .

## Browsers Verified In:
  * All Browsers .
## Steps To Reproduce:
* Visit https://www.semrush.com/redirect?url=ftp://evil.com:1337
* You will see a warning page only saying about the domain but no warning about the **protocol & Port** like below :- {F387701}
* But the source says it will take user to **ftp://evil.com:1337** not only **evil.com**

```
<a href="ftp://evil.com:1337" id="js-site-link" class="site_link" data-test-site-link="">
Go to site </a>
```
## Supporting Material/References:
* {F387701}
* {F387702}

## Impact

I noticed in **url=** parameter many protocols can be used . Like I can use **vnc://** protocol and on my mac os if I visit **https://www.semrush.com/redirect?url=ftp://evil.com:1337** and click on **Go to site** then it will open my mac environment's default VNC app like below screenshot :-
{F387702}

So while user may think they will visit a site but actually they will request to a site with a protocol what may take them to anything else .

##FIX :-
I can suggest 2 possible fix here :-
* Show the  **protocol & Ports** of the inputted url in the Warning page .
* Or only allow users to add **HTTP & HTTPS** protocol .

Thanks .

**Steps to Reproduce:**
* Visit https://www.semrush.com/redirect?url=ftp://evil.com:1337
* You will see a warning page only saying about the domain but no warning about the **protocol & Port** like below :- {F387701}
* But the source says it will take user to **ftp://evil.com:1337** not only **evil.com**

```
<a href="ftp://evil.com:1337" id="js-site-link" class="site_link" data-test-site-link="">
Go to site </a>
```
## Supporting Material/References:
* {F387701}
* {F387702}

**Proof of Concept:**
```
<a href="ftp://evil.com:1337" id="js-site-link" class="site_link" data-test-site-link="">
Go to site </a>
```

## Analysis / Response

**Vulnerability Class:** redirect
**CWE:** CWE-601
**Weakness:** Open Redirect
**Severity:** low
**Endpoint Pattern:** https://www.semrush.com/redirect?url=ftp://evil.com:1337

**Impact Assessment:**
I noticed in **url=** parameter many protocols can be used . Like I can use **vnc://** protocol and on my mac os if I visit **https://www.semrush.com/redirect?url=ftp://evil.com:1337** and click on **Go to site** then it will open my mac environment's default VNC app like below screenshot :-
{F387702}

So while user may think they will visit a site but actually they will request to a site with a protocol what may take them to anything else .

##FIX :-
I can suggest 2 possible fix here :-
* Show the  **protocol & Ports** of the inputted url in the Warning page .
* Or only allow users to add **HTTP & HTTPS** protocol .

Thanks .

**Remediation:**
Validate redirect URLs against an allowlist of permitted domains. Use relative URLs for internal redirects. Never place user input directly in redirect targets.

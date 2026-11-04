# SSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssrf
- cwe: CWE-918

## Scenario

How can emerging vectors like SSRF and insecure deserialization be chained into bigger impact, especially regarding modern protocol abuse [Ch 9: Emerging Attack Vectors]?

## Analysis / Response

## Overview
But this time the CSS will be imported from com/rpo/index.php/still/resource/rpo.css instead of the original one. The file content will remain the same but the content of the CSS will be replaced with a copy of the document instead and since the document is not a CSS file, the import will be ignored.

## Key points
It's pretty visible in the console that the content type was text/html. Let's see the content of the rpo.css file now: No prize for guessing, the CSS is actually the original document or the web page itself. Now, if we get the possibility of reaching an endpoint which displays any user-supplied input through the URL path, then we can easily inject our own CSS and even get XSS in some browsers. Controlling CSS Let's now go ahead and find out an endpoint for which we can control the content of the document.

## Approach
1. In practice, it's pretty visible in the console that the content type was text/html.
2. Typically, let's see the content of the rpo.css file now: No prize for guessing, the CSS is actually the original document or the web page itself.
3. Now, if we get the possibility of reaching an endpoint which displays any user-supplied input through the URL path, then we can easily inject our own CSS and even get XSS in some browsers.
4. In practice, controlling CSS Let's now go ahead and find out an endpoint for which we can control the content of the document.
5. When reviewing an application, a common example of such an endpoint is a search endpoint in which users enter a search term and it is reflected back to the web page alongside the results.

## Example
```
https://sandbox.prakharprasad.com/rpo/index.php has the following relative
   <html>
   <head>
       <title>RPO Demo</title>
       <link href="resource/rpo.css" rel="stylesheet" type="text/css"/>
```

## Scope & safety
Confirm findings on your own test accounts whenever possible and prefer non-destructive proofs.

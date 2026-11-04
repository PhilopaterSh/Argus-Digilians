# CSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: csrf
- cwe: CWE-352

## Scenario

How should I approach cross-site request forgery (CSRF) during an authorized assessment, especially regarding state-changing requests [Ch 4: Cross-site Request Forgery]?

## Analysis / Response

## Overview
Now, going back to external.html, add a new to-do item containing JavaScript, as illustrated by the following screenshot: Trying to inject JavaScript into a to-do app based on Node.js ones). The first alert is as follows: Successfully injected JavaScript part 1 The second alert is as follows: Successfully injected JavaScript part 1 Now that we have seen what can happen to our app if we suffered a CSRF attack, let's think about how such attacks can happen.

## Key points
Basically, such attacks can happen when our API endpoints (or URLs accepting the requests) are not protected at all. Attackers can exploit such vulnerabilities by simply observing which endpoints are used and attempt to exploit them by performing a basic HTTP POST operation to it. Basic defense against CSRF attacks If you are using modern frameworks or packages, the good news is that you can easily protect against such attacks by turning on or making use of CSRF protection. For example, for server.py, you can turn on xsrf_cookie by setting it to True, as illustrated by the following code:

## Approach
1. Basically, such attacks can happen when our API endpoints (or URLs accepting the requests) are not protected at all.
2. Attackers can exploit such vulnerabilities by simply observing which endpoints are used and attempt to exploit them by performing a basic HTTP POST operation to it.
3. Basic defense against CSRF attacks If you are using modern frameworks or packages, the good news is that you can easily protect against such attacks by turning on or making use of CSRF protection.
4. For example, for server.py, you can turn on xsrf_cookie by setting it to True, as illustrated by the following code:.

## Example
```
   The line changed is found at addTodo(); the highlighted code is the correct
    10. As usual, submit the item. Go to http://localhost:8080/api/ and refresh;
        you should see two alerts (or four alerts if you didn't delete the previous
   class Application(tornado.web.Application):
       def __init__(self):
```

## Scope & safety
Confirm findings on your own test accounts whenever possible and prefer non-destructive proofs.

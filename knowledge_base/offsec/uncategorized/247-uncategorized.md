# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What happens during '2.Dictionary Credential Attack' when solving 'AdventOfCyber2'?

## Analysis / Response

## 2.Dictionary Credential Attack
* First, we can turn on burpsuite and our proxy and go to the link
* When we enter a test username and password, we get the following request:
```
POST /login HTTP/1.1
Host: 10.10.181.49
Content-Length: 28
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
Origin: http://10.10.181.49
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Referer: http://10.10.181.49/
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9,ca;q=0.8
Connection: close

username=test&password=test1
```

* From here, we can do a dictionary attack in one of two ways:

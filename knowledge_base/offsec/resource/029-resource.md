# RESOURCE — h1

- source: h1
- class: resource
- cwe: CWE-400
- cve: ['CVE-2023-28755']
- severity: medium
- program: ibb
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2023-28755: ReDoS vulnerability in URI
**Affected Asset:** https://github.com/ruby

**Vulnerability Description:**
Original report on the Ruby program: https://hackerone.com/reports/1444501
Advisort: https://www.ruby-lang.org/en/news/2023/03/28/redos-in-uri-cve-[REDACTED_PHONE]/
NIST entry: https://nvd.nist.gov/vuln/detail/CVE-[REDACTED_PHONE]
CVSS:  7.5 high `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H` as listed by NIST but frankly I disagree with the `UI:N` part, I won't mind the extra 2k if you go with NIST but it didn't feel right not to mention it :) I filed the report with the CVSS I think this should have

Copy of the original report:

## Summary

Hello team, I hope you're doing well! The `URI` parser mishandles invalid URLs that have two `#` characters. It does correctly identify that they're invalid, but the regex performs very poorly and execution time grows much faster than the string length.

I found this somewhat accidentally when fuzzing for something else. I'm not sure if you care about such issues but I figured I'd report it anyway. The length of the strings required to actually cause the process to hang are very long, but it's not really an issue when the user-controlled input is sent in a request body.

## Steps to reproduce

Run the following script

```ruby
require 'benchmark'
require 'uri'

def parse(n)
  URI('https://example.com/dir/' + 'a' * n + '/##.jpg')
  rescue URI::InvalidURIError
  # Invalid URI because of the two #
end

n = 50000
Benchmark.bm(7) do |x|
  x.report('Base length') { parse(n) }
  x.report('Length x2  ') { parse(n * 2) }
  x.report('Length x4  ') { parse(n * 4) }
  x.report('Length x8  ') { parse(n * 8) }
end
```

Here's the output on my machine

```plaintext
              user     system      total        real
Base length  [REDACTED_PHONE])
Length x[REDACTED_PHONE])
Length x[REDACTED_PHONE])
Length x[REDACTED_PHONE])
```

We can see the execution time is roughly quintuples when the string length only doubles.

Here's my Ruby version

```shell
$ ruby -v
ruby 3.1.0p[REDACTED_PHONE] revision fb4df44d16) [x86_64-linux]
```

## Impact

High resource consumption, reduced performance, denial of service

**Steps to Reproduce:**
Run the following script

```ruby
require 'benchmark'
require 'uri'

def parse(n)
  URI('https://example.com/dir/' + 'a' * n + '/##.jpg')
  rescue URI::InvalidURIError
  # Invalid URI because of the two #
end

n = 50000
Benchmark.bm(7) do |x|
  x.report('Base length') { parse(n) }
  x.report('Length x2  ') { parse(n * 2) }
  x.report('Length x4  ') { parse(n * 4) }
  x.report('Length x8  ') { parse(n * 8) }
end
```

Here's the output on my machine

```plaintext
              user     system      total        real
Base length  [REDACTED_PHONE])
Length x[REDACTED_PHONE])
Length x[REDACTED_PHONE])
Length x[REDACTED_PHONE])
```

We can see the execution time is roughly quintuples 

## Analysis / Response

**Vulnerability Class:** resource
**CWE:** CWE-400
**Weakness:** Uncontrolled Resource Consumption
**Severity:** medium
**Endpoint Pattern:** https://hackerone.com/reports/1444501

**Impact Assessment:**
High resource consumption, reduced performance, denial of service

CVE-[REDACTED_PHONE]: ReDoS vulnerability in URI
Posted by hsbt on 28 Mar 2023

We have released the uri gem version 0.12.1, 0.11.1, 0.10.2 and 0.10.0.1 that has a security fix for a ReDoS vulnerability. This vulnerability has been assigned the CVE identifier CVE-[REDACTED_PHONE].

Details
A ReDoS issue was discovered in the URI component. The URI parser mishandles invalid URLs that have specific characters. It causes an increase in execution time for parsing strings to URI objects.

The uri gem version 0.12.0, 0.11.0, 0.10.1, 0.10.0 and all versions prior 0.10.0 are vulnerable for this vulnerability.

Recommended action
We recommend to update the uri gem to 0.12.1. In order to ensure compatibility with bundled version in older Ruby series, you may update as follows instead:

For Ruby 2.7: Update to uri 0.10.0.1
For Ruby 3.0: Update to uri 0.10.2
For Ruby 3.1: Update to uri 0.11.1
For Ruby 3.2: Update to uri 0.12.1
You can use gem update uri to update it. If you are using bundler, please add gem "uri", ">= 0.12.1" (or other version mentioned above) to your Gemfile.

Affected versions
uri gem 0.12.0
uri gem 0.11.0
uri gem 0.10.1
uri gem 0.10.0 or before

Credits
Thanks to Dominic Couture for discovering this issue.

Full Security Advisory: https://www.ruby-lang.org/en/news/2023/03/28/redos-in-uri-cve-[REDACTED_PHONE]/

**Remediation:**
Implement rate limiting and request size limits. Set timeouts on all operations. Use circuit breakers for downstream services. Validate input complexity.

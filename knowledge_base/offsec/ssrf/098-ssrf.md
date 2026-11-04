# SSRF — h1

- source: h1
- class: ssrf
- cwe: CWE-918
- severity: low
- program: bitwarden
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Blind HTTP GET SSRF via website icon fetch (bypass of pull#812)
**Affected Asset:** https://github.com/bitwarden

**Vulnerability Description:**
After a credential has been added to vault.bitwarden.com (or any self-hosted installation), if the settings allow website icons to be fetched (https://bitwarden.com/help/article/website-icons/), the Bitwarden server will try to fetch the icon image.

The relevant source code is https://github.com/bitwarden/server/blob/master/src/Icons/Controllers/IconsController.cs#L42-L65 and https://github.com/bitwarden/server/blob/master/src/Icons/Services/IconFetchingService.cs#L59
As we can see in the second link, just the domain is used as entrypoint to retrieve the icon image. After trying both HTTPS and HTTP connections, if an HTTP redirect happens the backend will try to follow it, for a maximum of 2 times.

The merged pull request https://github.com/bitwarden/server/pull/812 (which seems based on the vulnerable code snippet available on https://stackoverflow.com/a/8113687) tries to prevent SSRF attacks by checking if the domain resolves to a private IP, but that protection can be bypassed because not all IPs are checked: for example "0.0.0.0" (which will request "127.0.0.1") or the private subnet "[REDACTED_PHONE]/16" used in many cloud environments as metadata API (e.g. https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html) will pass that test and send the HTTP request to the private host.

### Proof-of-concept
0. Buy a domain and set it up on a server with a public IP address
1. Setup a webserver on the domain, e.g. nginx
2. Setup a malicious nameserver for the domain, I've used https://github.com/Crypt0s/FakeDns with the following configuration (change the domain name and IP with yours):

```
A www.yourdomain.com YOUR.PUBLIC.IP
A .*.local.yourdomain.com 0.0.0.0
```

4. Create a redirect index page on the newly created webserver, e.g. (change the domain name with yours):

```php
<?php
header("location: http://test.local.yourdomain.com/PATH_IS_KEPT");
exit();
```

3. Create a self-hosted Bitwarden instance following the instructions at https://bitwarden.com/help/article/install-on-premise/ and create an account
4. Log-in via cli on the `icons` docker instance and setup a dummy TCP listener on port 80, this will confirm we can request arbitrary HTTP endpoints on 127.0.0.1 
(**NOTE: i'm opening this socket just for PoC purposes -- of course the attacker wouldn't have such access however they could attack other locally-exposed services, such as the metadata API on [REDACTED_PHONE]**), e.g.:

```
# perl -MIO::Socket::INET -ne 'BEGIN{$l=IO::Socket::INET->new( LocalPort=>80,Proto=>"tcp",Listen=>5,ReuseAddr=>1); my $l=$l->accept(); while(<$l>){ print $_; }; close($l);}'
```

5. Log-in Bitwarden and add a credential with URL "www.yourdomain.com" (change the domain name with yours)


## Analysis / Response

**Vulnerability Class:** ssrf
**CWE:** CWE-918
**Weakness:** Server-Side Request Forgery (SSRF)
**Severity:** low
**Endpoint Pattern:** GET /PATH_IS_KEPT

**Impact Assessment:**
A malicious Bitwarden user can use the Bitwarden server to scan the local network and send arbitrary HTTP GET requests to a locally-exposed host, such as localhost or an endpoint in [REDACTED_PHONE]/16. The privilege to send such requests could potentially allow them to get hold of reserved information or escalate their privileges.

**Remediation:**
Here are my suggestions for the attack scenarios i have presented:
* Consider in the check all the potential private IPs which now pass it, for example I suggest to have a look at what GitLab does (it is Ruby code but readable) at https://gitlab.com/gitlab-org/gitlab-foss/-/blob/master/lib/gitlab/url_blocker.rb
* Verify the DNS resolution is not perfomed again after the IP is checked, if possible "lock" the HTTP request to the verified IP address so it is not sent using an unverified IP address

### Credits
Please credit "polict of Shielder" in your changelog/hall-of-fame for the discovery of this vulnerability.

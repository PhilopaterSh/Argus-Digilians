# PROTO_POLLUTION — h1

- source: h1
- class: proto_pollution
- cwe: CWE-79
- severity: high
- program: gitlab
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Stored XSS via Mermaid Prototype Pollution vulnerability
**Affected Asset:** gitlab.com

**Vulnerability Description:**
Affected Component: gitlab.com
Vulnerability Type: Cross-site Scripting (XSS) - Stored

Title: Stored XSS via Mermaid Prototype Pollution vulnerability
Weakness Type: Cross-site Scripting (XSS) - Stored

## Description
## Prologue

Gitlab supports Mermaid as part of GFM to allow users to generate diagrams and flowcharts from text.

In version 8.6.0, Mermaid added a support of directives to add more controll over styles(themes) applied to the diagrams.

You can read more about how this works here: https://mermaid-js.github.io/mermaid/diagrams-and-syntax-and-examples/directives.html

Syntax for declaring the directive is `%%{init: {<JSON_OBJECT>}}%%`

Directives can be used to overwrite default theme properties like `fontFamily` or `fontSize` to the graph.

Behind the scenes, library takes JSON_OBJECT from directive and merges it with config object. Later that config is used to generate new CSS rules:

```
  let userStyles = '';
  // user provided theme CSS
  if (cnf.themeCSS !== undefined) {
    userStyles += `\n${cnf.themeCSS}`;
  }
  // user provided theme CSS
  if (cnf.fontFamily !== undefined) {
    userStyles += `\n:root { --mermaid-font-family: ${cnf.fontFamily}}`;
  }
  // user provided theme CSS
  if (cnf.altFontFamily !== undefined) {
    userStyles += `\n:root { --mermaid-alt-font-family: ${cnf.altFontFamily}}`;
  }
```

## Vulnerability description

The issue is that directive JSON_OBJECT is lacking proper sanitization which means we can specify `__proto__` attribute to overwrite Object prototype.

For example, if we use following payload, it will add attribute `polluted` to every new object in the application:
```
%%{init: { '__proto__': {'polluted': 'asdf'}} }%%
sequenceDiagram
Alice->>Bob: Hi Bob
Bob->>Alice: Hi Alice
```

I have tried to use it to overwrite config values or other attributes to achieve XSS, but since a new attribute will be accessible in every object, it just breaks the application. 

## Steps to reproduce

1. Create an issue in any repository
2. Create mermaid diagram with following payload:
```
%%{init: { '__proto__': {'polluted': 'asdf'}} }%%
sequenceDiagram
Alice->>Bob: Hi Bob
Bob->>Alice: Hi Alice
```

3. Save the issue. Now when you open this page and click anywhere, you will see that nothing works. In Developer Console you can see a lot of exceptions that are triggered by a polluted prototype.

## PoC
Open https://gitlab.com/bugbountyuser1/dos/-/issues/1/
You will see that you can't comment or perform any action except clicking on the left sidebar links.

{F1200063}

## What is the current *bug* behavior?

Mermaid allows setting `__proto__` attribute in the directive which leads to DOS via prototype pollution.

## What is the expected *correct* behavior?

Mermaid doesn't allow` __proto_

## Analysis / Response

**Vulnerability Class:** proto_pollution
**CWE:** CWE-79
**Weakness:** Cross-site Scripting (XSS) - Stored
**Severity:** high
**Endpoint Pattern:** https://mermaid-js.github.io/mermaid/diagrams-and-syntax-and-examples/directives.html

**Impact Assessment:**
An attacker who can add Mermaid diagram to the page will make this page broken. Users will not be able to add comments, edit comments, etc.

**Remediation:**
Freeze Object.prototype. Use Map instead of plain objects for user-controlled keys. Validate and sanitize all object keys.

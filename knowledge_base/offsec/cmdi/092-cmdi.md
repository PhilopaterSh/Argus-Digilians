# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-78

## Scenario

From Chapter 16 (Network Application Protocols), section 'Domain Name System': Explain the key software security issues around Domain Name System. What should a code auditor look for?

## Analysis / Response

From a software security assessment perspective (Chapter 16: Network Application Protocols — Domain Name System), here is how auditors handle Domain Name System.

The Domain Name System (DNS) is a hierarchical distributed database that
implements a global naming scheme for resources available on the Internet. It
provides the infrastructure for mapping domain names to IP addresses as well as key
data used to interpret email addresses. When people access resources on the Internet,
they typically do so by using names such as www.google.com and
abuse@comcast.net. Their computers use DNS to translate these names into the IP
addresses suitable for use with Internet protocols. Obviously, text names are far
easier for people to work with than numbers. There's a reason you don't hear people
say "Man, 66.35.250.151 has really gone downhill lately."

Domain Names and Resource Records

The DNS database is organized as a tree data structure, with a single root node at the
top (see Figure 16-15 for a very simple example of such a tree). For the sake of clarity,
this diagram omits some domains that would be necessary to make the database
functional. Every node (and leaf) in the tree is called a domain, and a domain's child
nodes are called its subdomains. Each domain has a label, which is a short text
name such as com, mail, www, or food. A domain name is a series of labels,
separated by dots, that uniquely identifies a node in the tree by tracing the full path
from the specified domain to the root domain. For example, the domain name
www.google.com specifies a domain labeled www that's a subdomain of google.com.
The google.com domain is a subdomain of the com domain, and com is a subdomain
of the root domain. The root domain has an empty label, which is usually omitted in
casual discussion. In configuration files and technical discussions, however, it's
usually represented by a trailing dotwww.google.com., for example.

Figure 16-15. DNS tree data structure
 [View full size image]

Each domain owns a set of zero or more resource records, which describe attributes
of that domain. In general, you work with DNS by asking about a domain name. The
response you get is a set of resource records owned by that domain name. Every
resource record has five elements, described in Table 16-2.

Table 16-2. Resource Record Elements

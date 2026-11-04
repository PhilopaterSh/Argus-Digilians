# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

In the context of 'Common Threads', what important patterns and pitfalls related to Common Threads (part 2) should auditors watch for in application reviews?

## Analysis / Response

From a software security assessment perspective (Chapter 1: Software Vulnerability Fundamentals — Common Threads), here is how auditors handle Common Threads (part 2).

This process of tracing data flow is central to reviews of both the design and
implementation of software. User-malleable data presents a serious threat to the
system, and tracing the end-to-end flow of data is the main way to evaluate this
threat. Typically, you must identify where user-malleable data enters the system
through an interface to the outside world, such as a command line or Web request.
Then you study the different ways in which user-malleable data can travel through
the system, all the while looking for any potentially exploitable code that acts on the
data. It's likely the data will pass through multiple components of a software system
and be validated and manipulated at several points throughout its life span.

This process isn't always straightforward. Often you find a piece of code that's almost
vulnerable but ends up being safe because the malicious input is caught or filtered
earlier in the data flow. More often than you would expect, the exploit is prevented
only through happenstance; for example, a developer introduces some code for a
reason completely unrelated to security, but it has the side effect of protecting a
vulnerable component later down the data flow. Also, tracing data flow in a real-world
application can be exceedingly difficult. Complex systems often develop organically,
resulting in highly fragmented data flows. The actual data might traverse dozens of
components and delve in and out of third-party framework code during the process of
handling a single user request.

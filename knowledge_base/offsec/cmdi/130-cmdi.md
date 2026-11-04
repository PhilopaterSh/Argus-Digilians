# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-20

## Scenario

In the context of 'Auditing Application Protocols', what important patterns and pitfalls related to Debug should auditors watch for in application reviews?

## Analysis / Response

From a software security assessment perspective (Chapter 16: Network Application Protocols — Auditing Application Protocols), here is how auditors handle Debug.

Debugging messages were mentioned in the section on examining strings, and you
saw an example of debugging messages appearing in the compiled code. This means
you can turn on debugging and automatically receive all debugging output. Usually,
vendors have a command-line option to turn on debugging, but they might remove it
for the production release. However, if you cross-reference a debugging string such
as "Entering parse_message," you see a memory reference to where the debug
variable resides in memory. So you can just change it to nonzero at runtime and
receive all the debugging messages you need.

Find Communication Primitives

When all else fails, you can revert to finding entry points you know about; protocol
software has to send and receive data at some point. For protocols that operate over
TCP, entry points might include read(), recv(), recvmsg(), and WSArecv(). UDP
protocols might also use recvfrom() and WSArecvfrom(). Locating where these
functions are used points you to where data is read in from the network. Sometimes
this method is an easy route to identifying where data is being processed.
Unfortunately, it might take some tracing back through several functions, as many
applications make wrappers to communication primitives and use them indirectly (by
having the communication primitives in the form of class methods). Still, in these
cases, you can break on one of the aforementioned functions at runtime and let it
return a few times to see where processing is taking place.

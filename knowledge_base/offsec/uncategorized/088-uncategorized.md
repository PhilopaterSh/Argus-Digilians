# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What concrete techniques from software security assessment apply when reviewing Java?

## Analysis / Response

From a software security assessment perspective (Chapter 18: Web Technologies — Java), here is how auditors handle Java.

The Java Platform Enterprise Edition (formerly J2EE) includes a range of technologies
for Web application development. At the most basic level, Java provides the Servlet
API (javax.servlet) for interaction between a Web server and Java components. A
Java servlet is a Java class that runs inside a Web server and handles the
construction of dynamic responses to HTTP requests. The Web server has a
component called a servlet engine, or servlet container, that manages these servlets.
A Web developer installs a servlet in a Web server's servlet container, and then tells
the Web server which URLs and URL patterns that servlet should handle. When a
servlet handles a request, it can generate any kind of response it wants; much like a
CGI program can generate arbitrary responses. Servlets can also forward requests to
other servlets, which allows some interesting application designs.

Servlets give you the same kind of basic functionality that Web server APIs provide
(such as NSAPI and ISAPI). Even some of the more powerful customizations of
proprietary APIs are possible, as the newer versions of the Servlet API allow
developers to write filters, which can alter how the Web server handles every request
and response.

There are important differences between servlet technology and the proprietary Web
server APIs. First, the specification for the servlet interface is an open, published
standard with a reference implementation. Therefore, nearly every Web server
supports servlets in some form or another, which makes them an appealing
technology for large projects. Because servlets are written in cross-platform Java,
you can (in theory) take servlets written on one platform for one Web server and
move them to a completely different platform with a completely different Web server.
The use of Java also makes writing these Web server extensions much safer, as Java
is not vulnerable to the same memory corruption issues as proprietary C/C++ APIs.

Most Java Web applications present a front end by using JavaServer Pages (JSP). JSP
resembles other server-side scripting technologies, such as PHP or ASP, because you
use it to embed Java code in HTML documents. However, JSP is a little different
behind the scenes. When a Web server first receives a request for a JSP page, the
Web server always compiles that page into a servlet. This servlet is then cached, and

future requests for the original JSP page call that cached servlet. This behavior opens
some interesting design possibilities; for example, you can forward requests from a
servlet to a JSP page because JSP pages share the same characteristics as servlets.

Servlets and JSP represent the fundamental components of Java Web development.
On top of this foundation is an entire industry of frameworks, technologies, and
environments for developing and deploying Java applications. An entire book could be
devoted to covering the security aspects of any of these popular frameworks in detail.
However, for the sake of brevity, this chapter focuses on the core aspects of the Java
architecture. These patterns should help you understand the basic issues and apply
this knowledge to any framework you encounter.

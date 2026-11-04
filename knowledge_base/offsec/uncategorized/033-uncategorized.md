# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

In the context of 'Architecture', what should I know about Presentation Logic when performing a design or code-level security review?

## Analysis / Response

From a software security assessment perspective (Chapter 17: Web Applications — Architecture), here is how auditors handle Presentation Logic.

Presentation logic is code that's primarily concerned with displaying and formatting
data, as opposed to business- or application-oriented logic that's responsible for tasks
such as communicating with databases or authenticating users. Web application
development is often a collaborative effort between graphical designers and
application programmers, so this division can make sense from a logistical
perspective. If the presentation code can be cleanly divorced from the rest of the code,
Web application programmers can be responsible for performing the correct actions
on the back end and getting the correct data to the presentation logic, and the more
graphically oriented designers can be responsible for laying out the presentation of
the data and making sure it looks appealing.

In a Web application, this separation between presentation and application logic can
generally be accomplished by having each page first call into other code to perform
the necessary processing and gather the required data. The application programmer
creates this first part of the code, which is responsible for performing actions users
request and then filling out a data structure. The second part of the code, the
presentation logic, is responsible for rendering the contents of the data structure into
HTML.

XML can be used for this purpose, too; application developers can write code that
presents an XML document to the presentation logic. This presentation logic could be
an XSLT stylesheet written by a designer that instructs the server how to render the
data into HTML.

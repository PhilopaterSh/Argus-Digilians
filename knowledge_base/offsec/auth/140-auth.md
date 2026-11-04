# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe methodology and key techniques for Web Security for Developers — How the Internet Works: If the HTTP response is successful, the body contains the resource the during an authorized assessment.

## Analysis / Response

Based on Web Security for Developers (If the HTTP response is successful, the body contains the resource the):

If the HTTP response is successful, the body contains the resource the
        client was trying to access—often HyperText Markup Language (HTML) y
        describing the structure of the requested web page. In this case, the response
        contains styling information z as well as the page content itself {. Other
        types of responses may return JavaScript code, Cascading Style Sheets
        (CSS) used for styling HTML, or binary data in the body.

Stateful Connections
        Web servers typically deal with many user agents at once, but HTTP does
        nothing to distinguish which requests are coming from which user agent.
        This wasn’t an important consideration in the early days of the internet,
        because web pages were largely read-only. Modern websites, however, often
        allow users to log in and will track their activity as they visit and interact
        with different pages. To allow for this, HTTP conversations need to be
        made stateful. A connection or conversation between a client and a server
        is stateful when they perform a “handshake” and continue to send packets
        back and forth until one of the communicating parties decides to terminate
        the connection.
              When a web server wants to keep track of which user it’s responding to
        with each request, and thus achieve a stateful HTTP conversation, it needs
        to establish a mechanism to track the user agent as it makes the subsequent
        requests. The entire conversation between a particular user agent and a
        web server is called an HTTP session. The most common way of tracking ses-
        sions is for the server to send back a Set-Cookie header in the initial HTTP
        response. This asks the user agent receiving the response to store a cookie,
        a small snippet of text data pertaining to that particular web domain. The
        user agent then returns the same data in the Cookie header of any subse-
        quent HTTP request to the web server. If implemented correctly, the con-
        tents of the cookie being passed back and forth uniquely identify the user
        agent and hence establish the HTTP session.
              Session information contained in cookies is a juicy target for hackers.
        If an attacker steals another user’s cookie, they can pretend to be that user
        on the website. Similarly, if an attacker successfully persuades a website to
        accept a forged cookie, they can impersonate any user they please. We’ll
        look at various methods of stealing and forging cookies in Chapter 10.

                                                                  How the Internet Works   13

Use only on systems you are authorized to test; capture evidence and include remediation.

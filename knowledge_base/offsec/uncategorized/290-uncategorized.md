# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Walk me through From Day Zero to Zero Day — Mapping Code to Attack Surface: URI To locate routes quickly in a web application codebase, look for with practical steps from the source material.

## Analysis / Response

Based on From Day Zero to Zero Day (web-relevant) (URI To locate routes quickly in a web application codebase, look for):

URI To locate routes quickly in a web application codebase, look for
    URI-like strings. If you have a working instance of the application, try
    matching the behavior you observe at a particular route with the code
    that handles that route. Applications often handle routes declaratively,
    such as app.get('/items') instead of if (req.url === '/items'). Under-
    standing the declarative convention is key. Some frameworks, like Ruby
    on Rails, even centralize the routing logic in specific files, such as config/
    routes.rb.
    Headers Does the application check specific headers? Search for com-
    mon headers like Origin or Content-Type. Header parsing logic may occur
    at a higher level than individual controller code.
    Parameters How does the code extract parameters from a request?
    Other than the request URI, this is one of the most common sources of
    external input. Parameters can come from the HTTP request body (like
    the JSON content in the example request), the query string, or within
    the path.

Use only on systems you are authorized to test; capture evidence and include remediation.

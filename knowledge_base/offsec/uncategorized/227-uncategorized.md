# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

From Chapter 18 (Web Technologies), section 'CGI': Summarize a practical audit checklist for GET /scripts/..%c1%c1../winnt/system32/cmd.exe?/c+dir+c:\, including common vulnerable constructs and impact considerations.

## Analysis / Response

From a software security assessment perspective (Chapter 18: Web Technologies — CGI), here is how auditors handle GET /scripts/..%c1%c1../winnt/system32/cmd.exe?/c+dir+c:\.

This Unicode attack works because it inadvertently initiates an antiquated form of
HTTP request called an "indexed query." Indexed queries are old: They predate HTML
forms and today's GET and POST methods. (At one point, they were almost added to
the HTTP specification as the TEXTSEARCH query, but they never made it into the final
draft.) Before HTML had input boxes and buttons, you could place only a search box
on your Web site by using the <ISINDEX> tag on your page. It causes a single input text
box to be placed on your site, and still works if you want to see it in action. If a user
enters data in the box and presses Enter, the Web browser issues an indexed query to
the page. As an example, entering the string "jump car cake door" causes the browser
to send the following query:

The Web server interprets this indexed query by running page.exe with an argument
array argv[] of {"page.exe", "jump", "car", "cake", "door"} . The original string
delimiter was the addition sign, not the ampersand, but other than that, it's close to
the query string mechanism used today.

So when a contemporary Web server sees a request with a query string, it checks to
see whether it's an indexed query. If the query string contains an unescaped equal
sign (=), the Web server decides it's a normal GET query string request, puts the query
string in the QUERY_STRING environment variable, and doesn't pass any command-line
arguments to the CGI program.

If the Web server sees a query string without an equal sign, it assumes it's an indexed
query. It still places the entire query string in QUERY_STRING, but it also sets up
command-line arguments for running the CGI program.

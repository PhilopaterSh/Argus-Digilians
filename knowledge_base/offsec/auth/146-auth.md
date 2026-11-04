# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe the methodology and key techniques for Web Application Hacker's Handbook 2e — BinaryRead                  to access any of the information obtained by all the during an authorized assessment.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (BinaryRead                  to access any of the information obtained by all the):

BinaryRead                  to access any of the information obtained by all the
                                             other APIs.
                 HttpMethod                  Returns the method used in the HTTP request.
                 Browser                     Return details of the user’s browser, as submitted in
                                             the HTTP User-Agent header.
                 UserAgent
                 AcceptTypes                 Returns a string array of client-supported MIME types,
                                             as submitted in the HTTP Accept header.
                 UserLanguages               Returns a string array containing the languages
                                             accepted by the client, as submitted in the HTTP
                                             Accept-Language header.

               Session Interaction
               ASP.NET applications can interact with the user’s session to store and retrieve
               information in various ways.
                 The Session property provides a simple way to store and retrieve information
               within the current session. It is accessed in the same way as any other indexed
               collection:
                 Session[“MyName”] = txtMyName.Text;             // store user’s name
                 lblWelcome.Text = “Welcome “+Session[“MyName”]; // retrieve user’s name

                  ASP.NET proﬁles work much like the Session property does, except that they
               are tied to the user’s proﬁle and therefore actually persist across different ses-
               sions belonging to the same user. Users are reidentiﬁed across sessions either
               through authentication or via a unique persistent cookie. Data is stored and
               retrieved in the user proﬁle as follows:
                 Profile.MyName = txtMyName.Text;               // store user’s name
                 lblWelcome.Text = “Welcome “ + Profile.MyName; // retrieve user’s name

                The System.Web.SessionState.HttpSessionState class provides another
               way to store and retrieve information within the session. It stores information

c19.indd 719                                                                                           8/19/2011 12:18:35 PM

                                                                           Stuttard c19.indd V2 - 08/11/2011 Page 720

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

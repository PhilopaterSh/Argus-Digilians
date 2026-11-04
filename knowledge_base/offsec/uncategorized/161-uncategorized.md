# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Summarize how to identify, exploit (safely), and remediate issues related to: Web Application Hacker's Handbook 2e — 760   Chapter 20 n A Web Application Hacker’s Toolkit

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (760   Chapter 20 n A Web Application Hacker’s Toolkit):

760   Chapter 20 n A Web Application Hacker’s Toolkit

                Web Application Spiders
                Web application spiders work much like traditional web spiders. They request
                web pages, parse them for links to other pages, and then request those pages,
                continuing recursively until all of a site’s content has been discovered. To accom-
                modate the differences between functional web applications and traditional
                websites, application spiders must go beyond this core function and address
                various other challenges:
                   n   Forms-based navigation, using drop-down lists, text input, and other
                       methods
                   n   JavaScript-based navigation, such as dynamically generated menus
                   n   Multistage functions requiring actions to be performed in a deﬁned sequence
                   n   Authentication and sessions
                   n   The use of parameter-based identiﬁers, rather than the URL, to specify
                       different content and functionality
                   n   The appearance of tokens and other volatile parameters within the URL
                       query string, leading to problems identifying unique content

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

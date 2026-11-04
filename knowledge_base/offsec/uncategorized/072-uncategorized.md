# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

When auditing software for an authorized assessment, how should I approach DREAD Risk Ratings?

## Analysis / Response

From a software security assessment perspective (Chapter 2: Design Review — Threat Modeling), here is how auditors handle DREAD Risk Ratings.

Real-world applications are generally much larger and more complex in both design
and implementation than the examples used in this chapter. Increased size and
complexity creates a broad spectrum of attack vectors in a variety of user classes. As
a result, you can usually come up with a long list of potential threats and possible
recommendations to help mitigate those threats. In a perfect world, designers could
systematically go about addressing each threat and fixing potential issues, closing
each attack vector as necessary. However, certain business realities might not allow
mitigating every identified vector, and almost certainly not all at once. Clearly, some
sort of prioritization is needed to help address the more serious vectors before
worrying about the less important ones. By assigning a threat severity rating, you can
rank each uncovered threat based on the risk it poses to the security of the
application and associated systems. This rating can then be used as a guideline for
developers to help decide which issues take precedence.

You can choose to rate threats in a number of different ways. What's most important
is that you incorporate the exposure of the threat (how easy is it to exploit and who
the vector is available to) and the amount of damage incurred during a successful
exploit. Beyond that, you might want to add components that are more pertinent to
your environment and business processes. For this chapter's threat-modeling
purposes, the DREAD rating system developed by Microsoft is used. No model is
perfect, but this one provides a fairly good balance of commonly accepted threat
characteristics. These characteristics are briefly summarized as follows:

 Damage potential What are the repercussions if the threat is exploited
 successfully?
  Reproducibility How easy is it to reproduce the attack in question?
  Exploitability How difficult is it to perform the attack?
  Affected users If a successful attack is carried out, how many users would be
 affected and how important are they?
  Discoverability How difficult is it to spot the vulnerability?

Each category can be given a score between 1 and 10 (1 being the lowest, 10 the
highest). Category scores are then totaled and divided by 5 for an overall threat
rating. A rating of 3 or below can be considered a low-priority threat, 4 to 7 as a
medium-priority threat, and 8 or greater as a high-priority threat.

Note

The DREAD model is also useful in rating implementation and operational
vulnerabilities. In fact, you can use DREAD as your general-purpose rating system
over the entire course of an application review.

One of the benefits of the DREAD rating system is that it provides a range of detail you
can use when presenting results to business decision makers. You can give them a
concise threat assessment, with just the total threat rating and the category it falls
into. You could also present more detailed information, such as individual scores for
the five threat categories. You might even want to give them a full report, including
the model documentation and an explanation of how you arrived at the scores for
each category. Regardless of your choice, it's a good idea to have information
available at each level of detail when making a presentation to clients or senior
management.

Table 2-2 is an example of applying a DREAD rating to the brute-force login threat.

Table 2-2. Threat Summary with DREAD Rating

Threat Brute-force login.

Affected Web application login component.

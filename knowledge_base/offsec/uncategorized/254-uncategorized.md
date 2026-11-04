# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

In the context of 'Software Design Fundamentals', what important patterns and pitfalls related to Chain of Trust should auditors watch for in application reviews?

## Analysis / Response

From a software security assessment perspective (Chapter 2: Design Review — Software Design Fundamentals), here is how auditors handle Chain of Trust.

Chapter 1 also introduced the concept of transitive trust. Essentially, it
means that if component A trusts component B, component A must implicitly trust all
components trusted by component B. This concept can also be called a chain of trust
relationship.

A chain of trust is a completely viable security construct and the core of many
systems. Consider the way certificates are distributed and validated in a typical
Secure Sockets Layer (SSL) connection to a Web server. You have a local database of
signatures that identifies providers you trust. These providers can then issue a
certificate to a certificate authority (CA), which might then be extended to other
authorities. Finally, the hosting site has its certificate signed by one of these
authorities. You must follow this chain of trust from CA to CA when you establish an
SSL connection. The traversal is successful only when you reach an authority that's in
your trusted database.

Now say you want to impersonate a Web site for some nefarious means. For the
moment, leave Domain Name System (DNS) out of the picture because it's often an
easy target. Instead, all you want to do is find a way to manipulate the certificate
database anywhere in the chain of trust. This includes manipulating the client
certificate database of visitors, compromising the target site directly, or manipulating
any CA database in the chain, including a root CA.

It helps to repeat that last part, just to make sure the emphasis is clear. The transitive
nature of the trust shared by every CA means that a compromise of any CA allows an
attacker to impersonate any site successfully. It doesn't matter if the CA that issued
the real certificate is compromised because any certificate issued by a valid CA will
suffice. This means the integrity of any SSL transaction is only as strong as the
weakest CA. Unfortunately, this method is the best that's available for establishing a
host's identity.

Some systems can be implemented only by using a transitive chain of trust. As an
auditor, however, you want to look closely at the impact of choosing this trust model
and determine whether a chain of trust is appropriate. You also need to follow trusts
across all the included components and determine the real exposure of any
component. You'll often find that the results of using a chain of trust are complex and
subtle trust relationships that attackers could exploit.

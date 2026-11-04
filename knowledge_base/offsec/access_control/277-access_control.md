# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-284

## Scenario

What should a web pentester know about Web Application Hacker's Handbook 2e — 350   Chapter 9 n Attacking Data Stores?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (350   Chapter 9 n Attacking Data Stores):

350   Chapter 9 n Attacking Data Stores

                Common examples of LDAP are the Active Directory used within Windows
                domains, and OpenLDAP, used in various situations. You are most likely to
                encounter LDAP being used in corporate intranet-based web applications, such
                as an HR application that allows users to view and modify information about
                employees.
                   Each LDAP query uses one or more search ﬁlters, which determine the direc-
                tory entries that are returned by the query. Search ﬁlters can use various logical
                operators to represent complex search conditions. The most common search
                ﬁlters you are likely to encounter are as follows:
                   n   Simple match conditions match on the value of a single attribute. For
                       example, an application function that searches for a user via his username
                       might use this ﬁlter:

                       (username=daf)

                   n   Disjunctive queries specify multiple conditions, any one of which must
                       be satisﬁed by entries that are returned. For example, a search function
                       that looks up a user-supplied search term in several directory attributes
                       might use this ﬁlter:

                       (|(cn=searchterm)(sn=searchterm)(ou=searchterm))

                   n   Conjunctive queries specify multiple conditions, all of which must be
                       satisﬁed by entries that are returned. For example, a login mechanism
                       implemented in LDAP might use this ﬁlter:

                       (&(username=daf)(password=secret)

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

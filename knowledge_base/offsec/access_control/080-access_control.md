# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-284

## Scenario

Describe the methodology and key techniques for Web Application Hacker's Handbook 2e — Testing with Different User Accounts during an authorized assessment.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Testing with Different User Accounts):

Testing with Different User Accounts
               The easiest and most effective way to test the effectiveness of an application’s
               access controls is to access the application using different accounts. That way
               you can determine whether resources and functionality that can be accessed
               legitimately by one account can be accessed illegitimately by another.

                 HACK STEPS

                   1. If the application segregates user access to different levels of functional-
                      ity, first use a powerful account to locate all the available functionality.
                      Then attempt to access this using a lower-privileged account to test for
                      vertical privilege escalation.
                   2. If the application segregates user access to different resources (such as
                      documents), use two different user-level accounts to test whether access
                      controls are effective or whether horizontal privilege escalation is pos-
                      sible. For example, find a document that can be legitimately accessed by
                      one user but not by another, and attempt to access it using the second
                      user’s account — either by requesting the relevant URL or by submitting
                      the same POST parameters from within the second user’s session.

                  Testing an application’s access controls thoroughly is a time-consuming
               process. Fortunately, some tools can help you automate some of the work involved,
               to make your testing quicker and more reliable. This will allow you to focus
               on the parts of the task that require human intelligence to perform effectively.

c08.indd 267                                                                                         8/19/2011 12:08:32 PM

                                                                       Stuttard c08.indd V3 - 07/28/2011 Page 268

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

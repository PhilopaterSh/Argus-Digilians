# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Web Application Hacker's Handbook 2e — Chapter 4 n Mapping the Application          95

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Chapter 4 n Mapping the Application          95):

WahhBank.
                                                          login

                                                        WahhBank.
                                                          home

                  TransferFunds.         BillPayment.                BillPayment.       WahhBank.
                  selectAccounts          addPayee                   selectPayee         logout

                  TransferFunds.                                     BillPayment.
                   enterAmount                                       enterAmount

                 TransferFunds.                                       BillPayment.
                 confirmTransfer                                    confirmPayment

              Figure 4-10: A mapping of the functional paths within a web application

                 Representing an application’s functionality in this way is often more useful
              even in cases where the usual picture based on application pages can be applied
              without any problems. The logical relationships and dependencies between
              different functions may not correspond to the directory structure used within
              URLs. It is these logical relationships that are of most interest to you, both in
              understanding the application’s core functionality and in formulating possible
              attacks against it. By identifying these, you can better understand the expec-
              tations and assumptions of the application’s developers when implementing
              the functions. You also can attempt to ﬁnd ways to violate these assumptions,
              causing unexpected behavior within the application.
                 In applications where functions are identiﬁed using a request parameter, rather
              than the URL, this has implications for the enumeration of application content.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

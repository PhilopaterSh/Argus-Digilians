# AUTH — h1

- source: h1
- class: auth
- cwe: CWE-326
- severity: low
- program: sorare
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Mystery with a leaked token and Reusability of email confirmation link leading to Account Takeover
**Affected Asset:** sorare.com

**Vulnerability Description:**
Hi Team, 
First of all hope you are well and belated christmas wishes! Sorry for this long report. I need to write it long because many things happened during the testing and the report wont be complete if I didnt mention each and everything. During the test I end up modifying another user's profile. I'm sorry for that and I trust your safe harbor policy. 

If you dont want to read everything, please read the first part and must watch the Video POCs.

So here I'm with a mystery bug and I have a long story to tell. Please listen carefully. I was fed up not getting any bugs and was thinking to try my luck using google dorking. I tried many dorks and finally I came up with this one:

site:sorare.com inurl:token
=====================
{F2092332}

Here, as you can see there are two search results:

1. A random user's Email-confirmation link
2. A device confirmation link.
Both these links consists of tokens respective of the aim of these links. 

So, as I said earlier I was fed up and surfing without hope through these links. 
Now:
1. I opened up the second result which is of a confirm_device link with a token for a random user.
2. Initially the site said me the link is no longer valid and redirected to me to a settings option which asked me to upload profile picture.
3. Initially I thought that link was invalid and it got redirected me to my Sorare profile.
4. But it wasnt my profile.
5. The link brought me to a person named JACK3422's profile. Here I'd like to say thanks to Safe Harbor policy. Because I accidently changed the profile picture and some game settings the app asked me to do. Honestly I thought it is my profile.
=====================
6. So this leaked device confirmation link allowed me to get into a random person's profile.
7. Now I forgot to take a POC of this issue and was desparate. I logout from his profile and I tried to use that link again and it wasn't working again. :(
So I was about to quit. Before explaining further let me point out the steps worked here:

A. Google dorking using site:sorare.com inurl:token
B. Go to the second link, i.e; https://sorare.com/confirm_device?token=N04J3Zczv1GaFrniJisN1QgsisoJHQ
C. Click OK. It redirected me to that persons profile settings.

Unfortunately, the above link doesn't work anymore. So I decided to leave that sadly.
=====================

Then I opened the first link which is of a email confirmation link. You can guess its result. It was an expired confirmation link. But I have a behavior of trying IDOR everywhere even if it is a random encoded string.

Here  I'd like to mention the flow of Sorare sign up process:
A user enters email, username and password and on next step sorare sends a confirm email link to the entered ema

## Analysis / Response

**Vulnerability Class:** auth
**CWE:** CWE-326
**Weakness:** Inadequate Encryption Strength
**Severity:** low
**Endpoint Pattern:** https://sorare.com/confirm_device?token=N04J3Zczv1GaFrniJisN1QgsisoJHQ

**Impact Assessment:**
Even though the email confirmation links shows theyre expired they can be reused using this method. Since these links directly sign in users an attacker who got such a leaked link didnt want to know the password to sign in. So this is a highly dangerous bug. Leakage of these links can end up in account takeover easily. (As I did here using Google Dork)

**Remediation:**
Implement multi-factor authentication. Use secure session management. Apply account lockout policies. Never expose authentication logic client-side.

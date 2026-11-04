# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-284
- severity: medium
- program: gitlab
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Bypassing push rules via MRs created by Email
**Affected Asset:** gitlab.com

**Vulnerability Description:**
Hi GitLab Security Team,

GitLab EE has the feature of so-called push rules. An administrator, or more fine-grained per project, the owner can create certain push rules. The goal of these push rules is avoiding to push certain commits to the repository, which violate one of the push rules. If a commit violating one of the push rules is pushed to the repository, a pre-check gets executed, which decides a commit attempt should be rejected. Therefore, the user gets an error message indicating the commit does not follow the rules.

On the other hand, GitLab supports creating merge requests by writing an email address to a special address. If the email contains a `.patch` file as an attachment, the commits from this patch file are applied and pushed to the Repo. 

However, this step does not check for the push rules. This allows creating commits with content, that violates the configured push rules. It allows for example to push commits violating the commit message syntax, pushing an unsigned commit, pushing unwanted content (blacklisted secret files or bypassing regex), commits from unverified users, ...

## Steps to reproduce

Tested on GitLab.com 11.9.4-ee with a Gold Trial.

1. Create a repository with a Readme initialized
2. You then have to create one dummy merge request, e.g, by pushing some branch and create a new MR. The only purpose is that the empty state of `https://example.gitlab.com/<namespace>/<project>/merge_requests` does not show the incoming merge request email, which is required for the later steps.
3. Go to `https://example.gitlab.com/<namespace>/<project>/merge_requests`. At the bottom, there is a link opening a modal, which shows you the incoming merge request email. This email address looks similar to `incoming+<namespace>-<project-name>-<project-id>-<token>-[REDACTED_EMAIL]`
4. Configure the push rules of the project under `https://example.gitlab.com/<namespace>/<project>/settings/repository`
   * Check `Committer restriction`
   * Check `Reject unsigned commits`
   * Check `Check whether author is a GitLab user`
   * Check `Prevent committing secrets to Git`
   * Change `Commit message` to `Fixes \d+\..*`
   * Change `Commit message negative match` to `ssh\:\/\`
   * Change `Commit author's email` to `@example.com$`
   * Change `Prohibited file names` to `(jar|exe)$`
5. Now clone the repo locally
6. In the local repo, create a branch named `bypass`, create a new file `test.exe` and a new file `id_dsa`
7. Add all created file to the git repo and commit it (unsigned) with the commit message `Bypassing push rules ssh://foo.bar`
8. Create a git patch of the last commit by using the command `git format-patch -n HEAD^`
9. Open the patch file and change the `From` line to e.g. `Lin Jen <[REDACTED_EMAIL]>`. Of course, yo

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-284
**Weakness:** Improper Access Control - Generic
**Severity:** medium
**Endpoint Pattern:** https://example.gitlab.com/

**Impact Assessment:**
This allows anyone to bypass push rules set up by an administrator or project owner. This can lead to secrets being pushed to the repo, commits created by unknown users, etc

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.

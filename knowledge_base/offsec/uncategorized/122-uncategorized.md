# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Walk me through Enumerating Esoteric Attack Surfaces (Jann Moon): Github repo URL as an input and creates a wordlist based on the files with practical steps and examples from the source material.

## Analysis / Response

Based on Enumerating Esoteric Attack Surfaces (Jann Moon) (Github repo URL as an input and creates a wordlist based on the files):

Github repo URL as an input and creates a wordlist based on the files
  within it. This is beyond helpful for any targets using open-source
components and CMS that you can identify through fingerprinting. To
        use this silver bullet to slay your werewolves of choice:

                        pip3 install repolist

                     Very simple syntax seen below:

  repolist -u “https://github.com/octobercms/october” -o
                       octobercms_wordlist.txt

  You can even pipe it into ffuf, to immediately use it as your wordlist..

repolist -u "https://github.com/WordPress/WordPress" | ffuf
                 -u "http://example.com/FUZZ" -w -

If you want to trim some useless fat, you can stick to a certain branch (-b
       BRANCH_HERE) or just directories (-d) or files (-f) exclusively.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).

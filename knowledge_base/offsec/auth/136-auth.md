# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Enumerating Esoteric Attack Surfaces (Jann Moon): Docker or whatever workaround you devised, thinking it would be

## Analysis / Response

Based on Enumerating Esoteric Attack Surfaces (Jann Moon) (Docker or whatever workaround you devised, thinking it would be):

Docker or whatever workaround you devised, thinking it would be
     better, quicker, cheaper or easier. The only one that could be
 somewhat reasonably argued is “cheaper”, but that is only if the value
 that you place on your time is significantly lower than you should, for
                    the sake of your own self-esteem.

     I will assume you know how to maneuver through your Linux
 environment via Terminal and feel comfortable performing common
  user actions like moving throughout your file system, changing file
 permissions, installing tools through Github, Python and Golang and
common actions necessary to use Linux as an advanced user, a bar that
  appears high to the general public but anyone could get there in a
couple weeks with average effort. Basic Bash scripting is not required
but will definitely make your life easier through being able to automate
things and not having to remember every script and argument for the
    many tools you will use throughout your time as a vulnerability
researcher and hunter. Also, for most of the tools, I am saving the data
         to a file by piping the output by appending “ | tee -a
 tool-domain-output.txt”. If you want to be very powerful and super
             smart, you can use dark genius Hahwul’s gee
 (https://github.com/hahwul/gee), which is tee, but with many added
features like uncoloring text, filtering via built-in grep, splitting strings,
  converting the output to JSON, Markdown or HTML and more too.

Finally, in my Linux host, I always run as the “root” user. Since I am way
too busy to type “sudo” all the time (even with my alias of “s”) and I am
   way too smart to break anything by accident, I recommend you
become confident, fearless and value your time and become the actual
 owner of the piece of technology that YOU bought. Don’t let anyone
  tell you how to run your Linux sessions, unless they are offering you
absolute power without regret or restraint (like I am, right now). So you
won’t see much of “sudo” in this book, because I am a super user from
 the second I touch the keyboard and you should become a leader, by
                          following this advice.

Note: At the time of this writing (January 2024), the current version of
 Python is 3.12. There is a surprisingly high amount of scripts that are
 broken and won’t run with this version, so I generally install and run
Python tools with `python3.11` to avoid this error. You can try with 3.12
 but if the tool is vomiting error messages across your terminal, this is
the first thing I would try to do to fix it. This includes running setup via
   `python3.11 setup.py install` and `python3.11 -m pip install -r
                           requirements.txt`.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.

# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe methodology and key techniques for Web Security for Developers — Don’t Be an Accessory: As with anything useful on the internet, hackers have found ways to during an authorized assessment.

## Analysis / Response

Based on Web Security for Developers (As with anything useful on the internet, hackers have found ways to):

As with anything useful on the internet, hackers have found ways to
                   abuse <iframe> tags. Modern CSS allows page elements to be layered on top
                   of each other using the z-index attribute; elements with a higher z-index will
                   hide elements with a lower z-index and receive click events first. Page elements
                   can also be made transparent using the opacity attribute. By combining
                   these techniques, a hacker can position a transparent <div> over an <iframe>
                   element, and then trick a victim into clicking whatever content is stored in
                   the <div> rather than the underlying content they believe they are clicking.
                         This click-hijacking—clickjacking—has been used in a variety of ways.
                   In some cases, victims have been tricked into switching on their webcam so
                   the attacker can watch them remotely. Another variation of this technique
                   is likejacking, whereby a victim is tricked into liking something on Facebook
                   without their knowledge. Selling likes on the dark web for promotional pur-
                   poses is a big money-spinner for a hacker.

Use only on systems you are authorized to test; capture evidence and include remediation.

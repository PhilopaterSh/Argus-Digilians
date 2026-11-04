# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What tools and steps solve the forensics challenge 'BasedSteg'?

## Analysis / Response

# BasedSteg

> Steganography is the computer science of concealing or encrypting a message within a file, these are often found in ARG’s left by hackers. Find the message hidden within the image. [https://tinyurl.com/baseencryption](https://tinyurl.com/baseencryption)
No flag formatting required.

1. Download the image
2. We can see a very faint text at the bottom

    

3. Let's increase the brightness

    

4. The text says QmFzZWQgYW5kIHN0ZWdwaWxsZWQ=
    - Looks like base64... lets decode it
5. Our flag is Based and stegpilled

# INFO_DISCLOSURE — h1

- source: h1
- class: info_disclosure
- cwe: CWE-200
- severity: medium
- program: bumble
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Bumble API exposes read status of chat messages
**Affected Asset:** bma.bumble.com

**Vulnerability Description:**
# Summary
The Bumble app allows matches to chat with each other. In the mobile apps it is possible to see whether a message has been delivered (the webapp does not offer this feature), but the read status of messages is never disclosed. However, by issuing a POST request to the API endpoint at `https://am1.bumble.com/mwebapi.phtml?SERVER_OPEN_CHAT`, it is possible for users to retrieve the read status of individual message within all their chats.

# Steps to reproduce
1. Log in to the webapp at `https://bumble.com`.
2. Use an intercepting proxy (e.g. Burp Suite) to record traffic between the client and the server.
3. Open an existing chat.
4. Looking at the traffic log, notice an outgoing POST request to `https://am1.bumble.com/mwebapi.phtml?SERVER_OPEN_CHAT`, retrieving the chat messages from the backend.
5. Observe the response to the aforementioned request: it contains an array of `chat_messages`, where each `badoo.bma.ChatMessage` contains a boolean key `read`, displaying the read status of the message.

# Screenshots
**Chat A as shown in the iOS app**  *("bezorgd" is Dutch for "delivered")*
{F1161099}

**Chat B as shown in the iOS app**  *("bezorgd" is Dutch for "delivered")*
{F1161098}

**Request (and response) for chat A, showing that it has not been read by the other user**
{F1161096}

**Request (and response) for chat B, showing that it has been read by the other user**
{F1161097}

## Impact

The Bumble app implies that the read status of messages is not shared with others, due to the fact that it shows a "delivered" status below messages, while never showing a read status. Due to the information disclosure in the aforementioned API endpoint, users may view the read status of all messages within their chats, potentially violating the privacy of the user on the other end (who most likely expects this information to be kept private).

**Steps to Reproduce:**
1. Log in to the webapp at `https://bumble.com`.
2. Use an intercepting proxy (e.g. Burp Suite) to record traffic between the client and the server.
3. Open an existing chat.
4. Looking at the traffic log, notice an outgoing POST request to `https://am1.bumble.com/mwebapi.phtml?SERVER_OPEN_CHAT`, retrieving the chat messages from the backend.
5. Observe the response to the aforementioned request: it contains an array of `chat_messages`, where each `badoo.bma.ChatMessage` contains a boolean key `read`, displaying the read status of the message.

# Screenshots
**Chat A as shown in the iOS app**  *("bezorgd" is Dutch for "delivered")*
{F1161099}

**Chat B as shown in the iOS app**  *("bezorgd" is Dutch for "delivered")*
{F1161098}

**Request (and response) for chat A, showing that it has not been read by the other user**
{F1161096}

**Request (and response) for chat B, 

## Analysis / Response

**Vulnerability Class:** info_disclosure
**CWE:** CWE-200
**Weakness:** Information Disclosure
**Severity:** medium
**Endpoint Pattern:** https://am1.bumble.com/mwebapi.phtml?SERVER_OPEN_CHAT

**Impact Assessment:**
The Bumble app implies that the read status of messages is not shared with others, due to the fact that it shows a "delivered" status below messages, while never showing a read status. Due to the information disclosure in the aforementioned API endpoint, users may view the read status of all messages within their chats, potentially violating the privacy of the user on the other end (who most likely expects this information to be kept private).

The Bumble app allows matches to chat with each other. In the mobile apps it is possible to see whether a message has been delivered (the webapp does not offer this feature), but the read status of messages is never disclosed. However, by issuing a POST request to an API endpoint, it was possible for users to retrieve the read status of individual messages within all of their chats. Bumble has resolved this issue by always returning a read status of `false`, regardless of the actual read status of a message.

**Remediation:**
Remove sensitive data from error messages, headers, and responses. Implement proper access controls. Disable debug modes in production.

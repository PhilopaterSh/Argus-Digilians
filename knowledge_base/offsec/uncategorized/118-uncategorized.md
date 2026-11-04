# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do I apply 'From Day Zero to Zero Day — Taint Analysis: Once you resolve the dependency issues, dhcp6relay builds without er-' when testing an in-scope web application?

## Analysis / Response

Based on From Day Zero to Zero Day (web-relevant) (Once you resolve the dependency issues, dhcp6relay builds without er-):

Once you resolve the dependency issues, dhcp6relay builds without er-
rors, but you can’t run it:

terminate called after throwing an instance of 'std::system_error'
    what(): Unable to connect to redis (unix-socket): Cannot assign requested
    address
Aborted

     It appears that dhcp6relay is attempting to connect to a Redis server. If
you analyze configInterface.cpp, one of the source files for dhcp6relay, you’ll
see that it checks the DHCP_RELAY table in the CONFIG_DB database for a dhcpv6
_servers field name.
     Further research into this configuration setting leads to documentation
written by a SONiC developer (https://web.archive.org/web/20240224055552/
https://support.edge-core.com/hc/en-us/articles/8615164994201--Enterprise-SONiC
-DHCPv6-Relay) that contains the expected structure of this configuration
setting in the database.
     After resolving this requirement by adding the expected configuration
to the Redis database, dhcp6relay finally runs—but it doesn’t bind to any in-
terfaces because none of them contain non-link-local IPv6 addresses, as
prepare_socket requires. You need to create these manually and add this

Use only on systems you are authorized to test; capture evidence and include remediation.

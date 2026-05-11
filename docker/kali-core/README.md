# Argus Kali-Core

This container provides the security tool runtime for Argus.

It exposes SSH on port `22` inside the Docker network. The `argus-app` service connects to it with:

- Host: `kali-core`
- User: `kali`
- Password: `kali`

Installed tools:

- `ping`
- `curl`
- `wget`
- `whatweb`
- ProjectDiscovery `httpx`

The default password is for local Docker orchestration only. Change it before using this outside a local lab.

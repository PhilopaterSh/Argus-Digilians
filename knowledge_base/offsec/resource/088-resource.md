# RESOURCE — h1

- source: h1
- class: resource
- cwe: CWE-400
- severity: high
- program: rootstocklabs
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** DoS through PeerExplorer
**Affected Asset:** https://github.com/rsksmart/rskj

**Vulnerability Description:**
**Summary:** The peer discovery implementation is vulnerable to a Denial of Service attack due to improper management of connections.

**Description:** The two main files of interest in detailing this vulnerability are [PeerExplorer.java](https://github.com/rsksmart/rskj/blob/master/rskj-core/src/main/java/co/rsk/net/discovery/PeerExplorer.java) and [NodeChallengeManager.java](https://github.com/rsksmart/rskj/blob/master/rskj-core/src/main/java/co/rsk/net/discovery/NodeChallengeManager.java). To explain the flow of execution I'll be mentioning two theoretical nodes: an attacker, "N1" and a target, "N2".

When N1 sends an initial "ping" message to N2, N2 will reply with a "pong" message and a subsequent ping message to continue the handshake. After this, when N1 replies with a pong message, N2 will attempt to add N1 to its structure holding established connections. The relevant code snippets from `PeerExplorer.java` are below:
```    
public void handlePong(String ip, PongPeerMessage message) {
	PeerDiscoveryRequest request = this.pendingPingRequests.get(message.getMessageId());

	if (request != null && request.validateMessageResponse(message)) {
		this.pendingPingRequests.remove(message.getMessageId());
		NodeChallenge challenge = this.challengeManager.removeChallenge(message.getMessageId());
		if (challenge == null) {
			this.addConnection(message, ip, message.getPort());
		}
	}
}
...
private void addConnection(PongPeerMessage message, String ip, int port) {
	Node senderNode = new Node(message.getNodeId().getID(), ip, port);
	if (!StringUtils.equals(senderNode.getHexId(), this.localNode.getHexId())) {
		OperationResult result = this.distanceTable.addNode(senderNode);

		if (result.isSuccess()) {
			NodeID senderId = senderNode.getId();
			this.establishedConnections.put(senderId, senderNode);
			logger.debug("New Peer found ip:[{}] port[{}]", ip, port);
		} else {
			this.challengeManager.startChallenge(result.getAffectedEntry().getNode(), senderNode, this);
		}
	}
}
```
The `addConnection` method first attempts to add N1 to the `NodeDistanceTable` - a structure designed to hold a limited number of nodes (by default, 4096). If this insertion fails due to the target `NodeDistanceTable` bucket already being full, the attempted connection is instead added to `NodeChallengeManager`. The relevant code snippets from `NodeChallengeManager.java` are below:
```
public NodeChallenge startChallenge(Node challengedNode, Node challenger, PeerExplorer explorer) {
	PingPeerMessage pingMessage = explorer.sendPing(challengedNode.getAddress(), 1, challengedNode);
	String messageId = pingMessage.getMessageId();
	NodeChallenge challenge = new NodeChallenge(challengedNode, challenger, messageId);
	activeChallenges.put(messageId, challenge);
	return cha

## Analysis / Response

**Vulnerability Class:** resource
**CWE:** CWE-400
**Weakness:** Uncontrolled Resource Consumption
**Severity:** high
**Endpoint Pattern:** https://github.com/rsksmart/rskj/blob/master/rskj-core/src/main/java/co/rsk/net/discovery/PeerExplorer.java)

**Impact Assessment:**
An attacker could crash any RSKj node with peer discovery enabled (which it is by default).

**Remediation:**
This could be mitigated by implementing expiring challenges that are cleared by `PeerExplorerCleaner`.

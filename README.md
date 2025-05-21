# CTwobe - YouTube Covert Channel PoC

CTwobe is a **Proof of Concept** demonstration of using YouTube as a covert communication channel. This project showcases how YouTube's platform could theoretically be leveraged for command and control operations through video descriptions, comments, and encoding data into video frames.

**IMPORTANT: This tool is for educational and research purposes only. It is not intended for actual use in any unauthorized activities.**

## Concept Overview

CTwobe demonstrates three main covert channel techniques:

- Command and Control via Video Descriptions: Using YouTube video descriptions to transmit commands and receive results
- Data Exfiltration via Comments: Posting command results as comments on videos
- Binary Data Transfer via QR-Encoded Videos: Encoding files into QR code video frames and uploading as unlisted videos

## Practical Limitations

### YouTube API Quota Restrictions

This PoC is fundamentally impractical for real-world use due to severe YouTube API quota limitations:

- The YouTube API has strict daily quota limits (typically 10,000 units per day)
- Each operation consumes quota units:
    - Reading video information: ~1-3 units
    - Updating descriptions: ~50 units
    - Reading comments: ~1 unit per comment
    - Posting comments: ~50 units
    - Uploading videos: ~1600 units

A typical CTwobe operating session would exhaust daily quotas within minutes of active use, making it unsustainable for any practical application. (Although this can be bypassed using something like Selenium- however that is beyond the scope of this project)

### Other Significant Limitations

- **Authentication Requirements**: Requires OAuth credentials with extensive YouTube permissions
- **Performance**: The QR code video encoding/decoding process is extremely inefficient for data transfer
- **Account Risk**: Using this tool could result in YouTube account termination for Terms of Service violations

## Warning

This tool **should not be used** for:

- Actual penetration testing engagements
- Any unauthorized system access
- Malicious activities of any kind
- Circumventing platform security controls

## Legal Disclaimer

Usage of CTwobe for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, national, and international laws. I assume no liability and are not responsible for any misuse or damage caused by this program.
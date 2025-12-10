# GWT Deserializer
A small Python helper script for inspecting Google Web Toolkit (GWT) RPC requests and responses.
GWT-based applications still appear in legacy environments, and their RPC format is not pleasant to read during assessments. This tool extracts basic structure from raw RPC payloads to make analysis faster and less error-prone.

## Goal
The goal is to have a small, dependency-free utility focused purely on readability. It can be used on the fly during a pentest: copy the request body from Burp, pipe it into the script, and immediately see the header, string table, and resolved payload tokens. It is intentionally incomplete, but it significantly improves readability when triaging GWT endpoints.

## Features
General:
- Detects whether input appears to be a GWT RPC request or response.
- Works from stdin or from a file.
- No external dependencies.
For requests:
- Parses version, flags, and string table size.
- Extracts the string table and prints it with indexes.
- Resolves payload tokens to string table entries when possible.
For responses:
- Detects //OK / //EX prefixes.
- Attempts to JSON-decode the body and prints the resulting structure.
- Works from stdin or from a file.
- No external dependencies (Python 3 only).

## Installation
Clone the repository and make the script executable:
```text
git clone https://github.com/MSalmanN/gwt_deserializer
cd gwt_deserializer
chmod +x gwt_deserializer.py
```
## Design Notes
This script is not a full GWT RPC implementation.
It focuses on aspects most relevant during manual inspection:
- identifying the basic structure of RPC requests and responses
- exposing the string table
- mapping payload tokens back to string table entries when possible
- reducing time spent manually parsing long pipe-delimited RPC bodies
The aim is simplicity and readability rather than completeness.

## Limitations
- Does not implement the full GWT RPC serialization format  .
- Custom GWT serializers are not decoded.
- Java object graphs are not reconstructed.
- Response parsing assumes valid JSON after the `//OK` / `//EX` prefix.
- Some payload layouts may not be interpreted beyond basic token mapping.  

## Possible Future Work
- Helpers for extracting RPC bodies from proxied HTTP requests.  
- Burp Suite extension wrapper.
- Additional hints for common GWT RPC patterns (e.g., method positions).  
- Broader type handling for more complex payloads.
Contributions and ideas are welcome.

## License
This project is licensed under the **GNU General Public License v3.0**.

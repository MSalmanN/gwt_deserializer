#!/usr/bin/env python3
"""
gwt_deserializer.py

Quick-n-dirty helper for pentesters / testers to make GWT RPC
requests and responses more readable.

- Detects request vs response heuristically
- For requests:
    * Parses header (version, flags, string table size)
    * Extracts the string table
    * Shows the remaining payload as indexes / literals
- For responses:
    * Handles //OK / //EX prefix
    * Tries to JSON-decode the rest
    * Pretty-prints nested structures

Usage:
    echo "5|0|8|http://...|..." | python gwt_deserializer.py
    python gwt_deserializer.py sample.txt
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Tuple


def is_probable_gwt_response(data: str) -> bool:
    data = data.lstrip()
    return data.startswith("//OK") or data.startswith("//EX")


def is_probable_gwt_request(data: str) -> bool:
    # Very rough heuristic: lots of pipes and not starting with //OK/EX
    return "|" in data and not is_probable_gwt_response(data)


def parse_gwt_request(payload: str) -> Dict[str, Any]:
    """
    Parse a basic GWT-RPC request.

    Format (simplified, based on public docs):
      version|flags|stringTableSize|<string table entries...>|<payload...>|

    We decode:
      - header (version, flags, stringTableSize)
      - string table as index -> value
      - payload as remaining tokens (usually numeric indexes into string table)

    This is NOT a full spec implementation – it’s aimed at making traffic
    human-readable during testing.
    """
    raw = payload.strip().strip("|")
    parts = raw.split("|")

    result: Dict[str, Any] = {
        "kind": "request",
        "raw": payload.strip(),
        "header": {},
        "string_table": [],
        "payload_tokens": [],
        "notes": [
            "This is a *partial* GWT-RPC parser focused on readability.",
            "Header and string table should be accurate; payload interpretation is basic.",
        ],
    }

    if len(parts) < 3:
        result["error"] = "Not enough fields for a valid GWT-RPC request."
        return result

    try:
        version = int(parts[0])
        flags = int(parts[1])
        table_size = int(parts[2])
    except ValueError:
        result["error"] = "First three fields are not integers (version|flags|tableSize)."
        return result

    result["header"] = {
        "version": version,
        "flags": flags,
        "string_table_size": table_size,
    }

    # Extract string table
    string_start = 3
    string_end = string_start + table_size
    string_entries = parts[string_start:string_end]

    indexed_table = []
    for idx, value in enumerate(string_entries):
        indexed_table.append(
            {
                "index": idx,
                "value": value,
            }
        )

    result["string_table"] = indexed_table

    # Remaining tokens (usually indexes into string table or literals)
    remaining = parts[string_end:]
    interpreted_payload = []

    for token in remaining:
        if token == "":
            continue
        item: Dict[str, Any] = {"token": token}
        # Try to interpret as integer index into the string table
        try:
            num = int(token)
            if 0 <= num < len(indexed_table):
                item["as_index"] = num
                item["string_value"] = indexed_table[num]["value"]
        except ValueError:
            # Not an int – could be literal, boolean etc.
            if token in ("0", "1"):
                # Sometimes booleans are encoded as 0/1, but we already handled int above.
                pass
        interpreted_payload.append(item)

    result["payload_tokens"] = interpreted_payload

    return result


def parse_gwt_response(payload: str) -> Dict[str, Any]:
    """
    Parse a basic GWT-RPC response.

    Server-to-client GWT-RPC responses are usually:
      //OK[json...]
      //EX[json...]

    We:
      - capture the prefix (OK vs EX)
      - try to JSON-decode the rest
      - pretty print the structure
    """
    raw = payload.strip()
    prefix = raw[:4]  # e.g. "//OK" or "//EX"
    body = raw[4:]

    result: Dict[str, Any] = {
        "kind": "response",
        "raw": raw,
        "prefix": prefix,
        "status": "ok" if prefix.startswith("//OK") else "exception",
        "parsed_json": None,
        "json_error": None,
        "notes": [
            "GWT-RPC responses are typically JSON arrays with type info.",
            "This tool just makes them readable; you still need to interpret semantics.",
        ],
    }

    body = body.lstrip()
    try:
        parsed = json.loads(body)
        result["parsed_json"] = parsed
    except Exception as e:
        result["json_error"] = f"Failed to parse JSON: {e}"
        result["raw_body"] = body

    return result


def auto_parse(payload: str) -> Dict[str, Any]:
    """
    Decide whether this looks like a GWT request or response and parse accordingly.
    """
    if is_probable_gwt_response(payload):
        return parse_gwt_response(payload)
    elif is_probable_gwt_request(payload):
        return parse_gwt_request(payload)
    else:
        return {
            "kind": "unknown",
            "raw": payload.strip(),
            "error": "Does not look like GWT-RPC request or //OK//EX response.",
        }


def read_input(source: str = None) -> str:
    """
    Read input either from a file or stdin.
    """
    if source:
        with open(source, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    # Stdin
    return sys.stdin.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quick GWT-RPC request/response deserializer for pentesters."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="File containing raw GWT payload. If omitted, read from stdin.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print as indented JSON (default).",
    )
    parser.add_argument(
        "--raw-json",
        action="store_true",
        help="Only print parsed JSON body for GWT responses (if possible).",
    )
    args = parser.parse_args()

    data = read_input(args.file)

    result = auto_parse(data)

    if args.raw_json and result.get("kind") == "response" and result.get("parsed_json") is not None:
        print(json.dumps(result["parsed_json"], indent=2, ensure_ascii=False))
        return

    # Default: pretty JSON of our structured view
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime


def _default_dropped_path(out_path: str) -> str:
    if out_path.endswith(".json"):
        return out_path[:-5] + ".dropped.txt"
    if out_path.endswith(".ndjson"):
        return out_path[:-6] + ".dropped.txt"
    return out_path + ".dropped.txt"


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "command failed:\n"
            f"  cmd: {' '.join(cmd)}\n"
            f"  exit: {proc.returncode}\n"
            f"  stderr: {proc.stderr.strip()}"
        )
    return proc.stdout


def _extract_json_payload(line: str) -> str | None:
    """
    Docker compose logs often prefixes like:
      template_api-app-1  | {"timestamp": "...", ...}
    We strip the prefix and return the raw JSON part.
    """

    s = line.strip()
    if not s:
        return None

    if "|" in s:
        # Keep everything after the first pipe.
        s = s.split("|", 1)[1].strip()

    # Best-effort: only accept lines that look like JSON objects.
    if not (s.startswith("{") and s.endswith("}")):
        return None
    return s


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export Docker Compose service logs as clean JSON (ndjson or array)."
        )
    )
    parser.add_argument(
        "--compose-cmd",
        default="docker compose",
        help='Compose command to use, e.g. "docker compose" or "docker-compose".',
    )
    parser.add_argument("--service", default="app", help="Service name (default: app).")
    parser.add_argument("--tail", type=int, default=200, help="How many lines to tail.")
    parser.add_argument(
        "--out",
        default="app-logs.json",
        help="Output file path (default: app-logs.json).",
    )
    parser.add_argument(
        "--format",
        choices=("ndjson", "array"),
        default="ndjson",
        help="Output format: ndjson (one JSON per line) or array (single JSON array).",
    )
    parser.add_argument(
        "--dropped-out",
        default="",
        help=(
            "Optional path to write dropped/non-JSON lines "
            "(e.g. app-logs.dropped.txt). "
            "If omitted, a default derived from --out is used when there are "
            "dropped lines."
        ),
    )

    args = parser.parse_args()

    compose_parts = args.compose_cmd.split()
    cmd = compose_parts + [
        "logs",
        "--tail",
        str(args.tail),
        "--no-log-prefix",
        args.service,
    ]

    raw = _run(cmd)
    records: list[dict] = []
    dropped = 0
    dropped_lines: list[str] = []

    for line in raw.splitlines():
        payload = _extract_json_payload(line)
        if payload is None:
            dropped += 1
            dropped_lines.append(line)
            continue
        try:
            records.append(json.loads(payload))
        except json.JSONDecodeError:
            dropped += 1
            dropped_lines.append(line)

    meta = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "service": args.service,
        "tail": args.tail,
        "format": args.format,
        "parsed": len(records),
        "dropped": dropped,
        "compose_cmd": args.compose_cmd,
    }

    if args.format == "array":
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(
                {"meta": meta, "records": records},
                f,
                ensure_ascii=False,
                indent=2,
            )
            f.write("\n")
    else:
        # NDJSON: first line is meta, then each record as a JSON line.
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(json.dumps({"meta": meta}, ensure_ascii=False) + "\n")
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    dropped_out = args.dropped_out.strip()
    if dropped_lines:
        if not dropped_out:
            dropped_out = _default_dropped_path(args.out)
        with open(dropped_out, "w", encoding="utf-8") as f:
            for line in dropped_lines:
                f.write(line.rstrip("\n") + "\n")

    msg = f"Wrote {len(records)} JSON log records to {args.out} (dropped {dropped})"
    if dropped_lines:
        msg += f"; dropped lines saved to {dropped_out}"
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

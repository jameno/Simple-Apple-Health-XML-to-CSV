#!/usr/bin/env python3
"""
Simple Apple Health XML to CSV.

Converts the Apple Health export.xml into a single CSV. Streams in constant
memory; standard library only.

Usage:
    python3 apple_health_xml_convert.py
    python3 apple_health_xml_convert.py --input PATH --output OUT.csv

Without arguments, reads ./export.zip, ./apple_health_export/export.xml, or
./export.xml (whichever it finds first) and writes
./apple_health_export_YYYY-MM-DD.csv.
"""

import argparse
import csv
import datetime as dt
import io
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# Columns the legacy script kept up-front for readability.
SHIFTED_COLS = [
    "type", "sourceName", "value", "unit",
    "startDate", "endDate", "creationDate",
]
# These were also pinned to the front by the legacy script when present.
LOOP_KIT_KEYS = (
    "com.loopkit.InsulinKit.MetadataKeyProgrammedTempBasalRate",
    "com.loopkit.InsulinKit.MetadataKeyScheduledBasalRate",
    "com.loudnate.CarbKit.HKMetadataKey.AbsorptionTimeMinutes",
)


def auto_detect_input():
    cwd = Path.cwd()
    for c in (
        cwd / "export.zip",
        cwd / "apple_health_export" / "export.xml",
        cwd / "export.xml",
    ):
        if c.exists():
            return c
    return None


def open_export(input_path):
    """Open export.xml as a binary stream. Accepts .zip, .xml, or a folder."""
    input_path = Path(input_path)
    if input_path.is_dir():
        xml = input_path / "export.xml"
        if not xml.exists():
            raise SystemExit(f"no export.xml inside {input_path}")
        return open(xml, "rb"), None
    if input_path.suffix.lower() == ".zip":
        zf = zipfile.ZipFile(input_path)
        candidates = [n for n in zf.namelist()
                      if n.endswith("/export.xml") or n == "export.xml"]
        if not candidates:
            zf.close()
            raise SystemExit(f"no export.xml inside {input_path}")
        # Prefer the shortest path (typically apple_health_export/export.xml).
        return zf.open(min(candidates, key=len)), zf
    return open(input_path, "rb"), None


def stream_clean(input_path):
    """Yield XML byte chunks: skips the inline DOCTYPE, strips \\x0b.

    Apple's export has both quirks; ElementTree refuses to parse without
    cleanup, but doing it inline avoids writing a multi-GB temp copy.
    """
    fh, owner = open_export(input_path)
    try:
        head = b""
        while len(head) < 128 * 1024:
            chunk = fh.read(128 * 1024 - len(head))
            if not chunk:
                break
            head += chunk
        doctype_start = head.find(b"<!DOCTYPE")
        if doctype_start < 0:
            yield head.replace(b"\x0b", b"")
        else:
            dtd_end = head.find(b"]>", doctype_start)
            if dtd_end < 0:
                raise SystemExit("DOCTYPE not closed within first 128 KB")
            yield head[:doctype_start].replace(b"\x0b", b"")
            yield head[dtd_end + 2:].replace(b"\x0b", b"")
        while True:
            chunk = fh.read(64 * 1024)
            if not chunk:
                break
            yield chunk.replace(b"\x0b", b"")
    finally:
        fh.close()
        if owner is not None:
            owner.close()


class _GenIO(io.RawIOBase):
    """Adapt a bytes-yielding generator to a readable file-like for ET.iterparse."""

    def __init__(self, gen):
        self._gen = gen
        self._buf = bytearray()
        self._eof = False

    def readable(self):
        return True

    def readinto(self, dst):
        n = len(dst)
        while not self._eof and len(self._buf) < n:
            try:
                chunk = next(self._gen)
            except StopIteration:
                self._eof = True
                break
            if chunk:
                self._buf.extend(chunk)
        out = min(n, len(self._buf))
        if out:
            dst[:out] = bytes(self._buf[:out])
            del self._buf[:out]
        return out


def iter_attribs(input_path):
    """Yield each XML element's live attrib dict on its end event.

    The yielded dict is the element's actual attrib, not a copy — the
    generator clears the element only after the consumer is done with it.
    Callers must not retain the dict across iterations. Saves ~7.5M dict
    allocations on a 1 GB export.

    Memory-bounded: finished top-level elements (depth 2 — direct children of
    <HealthData>) are dropped from the root. Inner elements are cleared but
    stay attached to their immediate parent until that parent ends, bounded
    by max children-per-element (small in Apple's schema).
    """
    stream = _GenIO(stream_clean(input_path))
    context = ET.iterparse(stream, events=("start", "end"))
    ctx = iter(context)
    _, root = next(ctx)
    depth = 1
    for event, elem in ctx:
        if event == "start":
            depth += 1
        else:
            yield elem.attrib
            elem.clear()
            depth -= 1
            if depth == 1:
                del root[0]


def strip_type_prefix(value):
    if not value:
        return value
    for prefix in ("HKQuantityTypeIdentifier", "HKCategoryTypeIdentifier"):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value


def rename_column(name):
    return name.replace("HKCharacteristicTypeIdentifier", "")


def discover_columns(input_path):
    keys = set()
    for attribs in iter_attribs(input_path):
        keys.update(attribs)
    return keys


def write_csv(input_path, output_csv, quiet=False):
    if not quiet:
        print("scanning columns…", file=sys.stderr, flush=True)
    keys = discover_columns(input_path)

    rename_map = {k: rename_column(k) for k in keys}
    renamed = set(rename_map.values())

    shifted = [c for c in SHIFTED_COLS if c in renamed]
    loop = [c for c in LOOP_KIT_KEYS if c in renamed]
    rest = sorted(renamed - set(shifted) - set(loop))
    fields = shifted + loop + rest

    # Precompute input-key → output-column-index for fast row construction.
    field_to_idx = {f: i for i, f in enumerate(fields)}
    key_to_idx = {k: field_to_idx[rename_map[k]] for k in keys}
    n_cols = len(fields)
    type_idx = field_to_idx.get("type")

    if not quiet:
        print(f"writing {n_cols} columns…", file=sys.stderr, flush=True)

    n_rows = 0
    with open(output_csv, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(fields)
        for attribs in iter_attribs(input_path):
            row = [""] * n_cols
            for k, v in attribs.items():
                row[key_to_idx[k]] = v
            if type_idx is not None and row[type_idx]:
                row[type_idx] = strip_type_prefix(row[type_idx])
            writer.writerow(row)
            n_rows += 1
    return n_rows, len(fields)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Convert Apple Health export.xml to a single CSV.",
    )
    ap.add_argument(
        "-i", "--input", default=None,
        help="export.zip, export.xml, or apple_health_export/ folder. "
             "Default: looks in the current directory.",
    )
    ap.add_argument(
        "-o", "--output", default=None,
        help="Output CSV path. Default: ./apple_health_export_YYYY-MM-DD.csv.",
    )
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="Suppress progress messages.")
    args = ap.parse_args(argv)

    if args.input:
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            raise SystemExit(f"input not found: {input_path}")
    else:
        input_path = auto_detect_input()
        if input_path is None:
            raise SystemExit(
                "no Apple Health export found in the current directory.\n"
                "  drop your export.zip here and re-run, or\n"
                "  pass an explicit path: --input PATH"
            )

    if args.output:
        output_csv = Path(args.output).resolve()
    else:
        today = dt.datetime.now().strftime("%Y-%m-%d")
        output_csv = Path.cwd() / f"apple_health_export_{today}.csv"

    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not args.quiet:
        print(f"input:  {input_path}", file=sys.stderr)
        print(f"output: {output_csv}", file=sys.stderr)

    t0 = time.perf_counter()
    rows, cols = write_csv(input_path, output_csv, quiet=args.quiet)
    if not args.quiet:
        print(f"wrote {rows:,} rows × {cols} cols in {time.perf_counter() - t0:.1f}s",
              file=sys.stderr)


if __name__ == "__main__":
    main()

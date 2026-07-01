#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Apple Health XML to CSV
==============================
:File: convert.py
:Description: Convert Apple Health "export.xml" file into a csv
:Version: 0.0.3
:Created: 2019-10-04
:Updated: 2026-06-30
:Authors: Jason Meno (jam)
:Dependencies: An export.xml file from Apple Health
:License: BSD-2-Clause
"""

# %% Imports
import argparse
import os
import sys
import datetime as dt
import tempfile
import xml.etree.ElementTree as ET

import pandas as pd

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


# %% Function Definitions

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Apple Health export.xml to a dated CSV file."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="export.xml",
        help="Path to the Apple Health export.xml file (default: export.xml)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help=(
            "Output CSV file path. "
            "Defaults to apple_health_export_<YYYY-MM-DD>.csv in the current directory."
        ),
    )
    return parser.parse_args()


def preprocess_to_temp_file(file_path):
    """
    The export.xml file is where all your data is, but Apple Health Export has
    two main problems that make it difficult to parse:
        1. The DTD markup syntax is exported incorrectly by Apple Health for some data types.
        2. The invisible character \\x0b (sometimes rendered as U+000b) likes to destroy trees.
           Think of the trees!

    Knowing this, we can save the trees and pre-process the XML data to avoid
    destruction and ParseErrors.

    Returns the path to a temporary pre-processed file that the caller is
    responsible for deleting.
    """
    print("Pre-processing and writing to temporary file...", end="", flush=True)

    # Use a named temporary file so it is automatically deleted if the process
    # is interrupted unexpectedly (on most OSes).
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="UTF-8",
        suffix=".xml",
        delete=False,
        prefix="apple_health_tmp_",
    )
    temp_file_path = tmp.name

    try:
        with open(file_path, "r", encoding="UTF-8") as infile:
            skip_dtd = False
            for line in infile:
                if "<!DOCTYPE" in line:
                    skip_dtd = True
                if not skip_dtd:
                    line = strip_invisible_character(line)
                    tmp.write(line)
                if "]>" in line:
                    skip_dtd = False
    finally:
        tmp.close()

    print("done!")
    return temp_file_path


def strip_invisible_character(line):
    """Remove the invisible vertical-tab character that breaks XML parsing."""
    return line.replace("\x0b", "")


def xml_to_csv(file_path):
    """Iterate over the element tree, collecting all element attributes, then
    combine them into a single DataFrame.

    Uses a memory-efficient iterparse strategy that clears both the processed
    element *and* its parent (root) after each 'end' event, preventing the
    unbounded memory growth that plain iterparse suffers with large files.
    """
    print("Converting XML File to CSV...", end="", flush=True)

    attribute_list = []
    root = None

    iterator = ET.iterparse(file_path, events=("start", "end"))

    if TQDM_AVAILABLE:
        iterator = tqdm(iterator, desc="  Parsing elements", unit=" elem", leave=False)

    for event, elem in iterator:
        if event == "start" and root is None:
            # Capture the root element so we can clear it to free memory
            root = elem
            continue

        if event == "end":
            child_attrib = dict(elem.attrib)  # copy so clear() doesn't wipe it

            for metadata_entry in list(elem):
                metadata_values = list(metadata_entry.attrib.values())
                if len(metadata_values) == 2:
                    metadata_dict = {metadata_values[0]: metadata_values[1]}
                    child_attrib.update(metadata_dict)
                else:
                    # Log unexpected metadata shapes instead of silently dropping
                    if metadata_values:
                        print(
                            f"\n  [warn] Skipping metadata entry with unexpected "
                            f"value count ({len(metadata_values)}): {metadata_values}",
                            file=sys.stderr,
                        )

            attribute_list.append(child_attrib)

            # Clear processed element AND its parent (root) to prevent the
            # classic iterparse memory leak where the root accumulates all children.
            elem.clear()
            if root is not None:
                root.clear()

    health_df = pd.DataFrame(attribute_list)

    # Every health data type and some columns have a long identifier prefix.
    # Remove these for readability.
    health_df["type"] = (
        health_df["type"]
        .str.replace("HKQuantityTypeIdentifier", "", regex=False)
        .str.replace("HKCategoryTypeIdentifier", "", regex=False)
    )
    health_df.columns = health_df.columns.str.replace(
        "HKCharacteristicTypeIdentifier", "", regex=False
    )

    # Parse date columns to proper datetime objects for easier downstream analysis
    for date_col in ("startDate", "endDate", "creationDate"):
        if date_col in health_df.columns:
            health_df[date_col] = pd.to_datetime(
                health_df[date_col], errors="coerce"
            )

    # Parse value column to numeric where possible
    if "value" in health_df.columns:
        health_df["value"] = pd.to_numeric(health_df["value"], errors="coerce")

    # Reorder columns for easier visual data review
    original_cols = list(health_df.columns)
    shifted_cols = [
        "type",
        "sourceName",
        "value",
        "unit",
        "startDate",
        "endDate",
        "creationDate",
    ]

    # Add Loop-specific column ordering if metadata entries exist
    loop_cols = [
        "com.loopkit.InsulinKit.MetadataKeyProgrammedTempBasalRate",
        "com.loopkit.InsulinKit.MetadataKeyScheduledBasalRate",
        "com.loudnate.CarbKit.HKMetadataKey.AbsorptionTimeMinutes",
    ]
    for col in loop_cols:
        if col in original_cols:
            shifted_cols.append(col)

    remaining_cols = [c for c in original_cols if c not in shifted_cols]
    reordered_cols = [c for c in shifted_cols if c in original_cols] + remaining_cols
    health_df = health_df.reindex(labels=reordered_cols, axis="columns")

    # Sort by newest data first
    if "startDate" in health_df.columns:
        health_df.sort_values(by="startDate", ascending=False, inplace=True)

    print("done!")
    return health_df


def save_to_csv(health_df, output_path=None):
    """Write the health DataFrame to a CSV file.

    Args:
        health_df: The DataFrame to save.
        output_path: Explicit destination path. When None, defaults to
                     apple_health_export_<YYYY-MM-DD>.csv in the current directory.
    """
    print("Saving CSV file...", end="", flush=True)

    if output_path is None:
        today = dt.datetime.now().strftime("%Y-%m-%d")
        output_path = f"apple_health_export_{today}.csv"

    health_df.to_csv(output_path, index=False)
    print(f"done!  →  {os.path.abspath(output_path)}")


def remove_temp_file(temp_file_path):
    """Delete the temporary pre-processed XML file."""
    print("Removing temporary file...", end="", flush=True)
    try:
        os.remove(temp_file_path)
        print("done!")
    except OSError as exc:
        print(f"warning: could not remove temp file '{temp_file_path}': {exc}", file=sys.stderr)


def main():
    args = parse_args()

    file_path = args.input

    # Validate input file up front to give a clear error message
    if not os.path.exists(file_path):
        print(f"Error: Input file '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(file_path):
        print(f"Error: '{file_path}' is not a file.", file=sys.stderr)
        sys.exit(1)

    temp_file_path = preprocess_to_temp_file(file_path)
    try:
        health_df = xml_to_csv(temp_file_path)
        save_to_csv(health_df, output_path=args.output)
    except ET.ParseError as exc:
        print(f"\nError: Failed to parse XML — {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\nUnexpected error: {exc}", file=sys.stderr)
        raise
    finally:
        remove_temp_file(temp_file_path)


# %%
if __name__ == "__main__":
    main()

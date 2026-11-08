"""CSV manifest writer

Writes a single CSV file for completed extraction run. All sensor data is
written to a single CSV file, one row per frame.

Output CSV:
    Uses , as delimiter, " as enclosure, and \\ as escape character.

    Columns:
        filename        - mandatory, name of the file the metadata
                          belongs to
        timestamp       - date time where file was taken
        ...             - any other sensor data that was available in the spec file
"""

import csv
from pathlib import Path

from ..models.core import FrameMetadata

def _build_csv_row(path: Path, meta: FrameMetadata) -> dict:
    """Build a CSV row dictionary from FrameMetadata.

    Args:
        path:   Path to the written frame file.
        meta:   FrameMetadata with sensor_snapshot and project_metadata.

    Returns:
        Dict suitable for DictWriter with BIIGLE-compatible keys.
    """
    row = {
        "filename": path.name,
        "timestamp": meta.utc_timestamp.strftime("%Y-%m-%d %H:%M:%SZ"),
    }
    
    row.update(meta.sensor_snapshot)

    return row


def write_csv_manifest(
    written: list[tuple[Path, FrameMetadata]],
    output_dir: Path,
) -> Path:
    """Write a CSV file for a completed extraction run.

    Builds one entry per frame keyed by filename, assembles CSV entries from
    project_metadata shared across all frame, and writes to CSV.

    Entries are sorted by utc timestamp.

    Args:
        written:    list of (path, FrameMetadata) pairs - as returned by
                    output_frames, or collected from workers.
        output_dir: directory where manifest will be written, must exist.

    Returns:
        Path to the written CSV file

    Raises:
        OSError:    if the file cannot be written.
    """
    written = sorted(written, key=lambda pair: pair[1].utc_timestamp)

    # Build all rows first to determine which columns are actually used
    rows = [_build_csv_row(path, meta) for path, meta in written]

    manifest_path = output_dir / "metadata.csv"

    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(),
                                delimiter=",", quotechar='"',
                                escapechar="\\", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    return manifest_path

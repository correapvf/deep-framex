import csv
import pytest
from datetime import datetime, timezone
from pathlib import Path

from deep_framex.metadata.csv import _build_csv_row, write_csv_manifest
from deep_framex.models.core import FrameMetadata


def make_meta(utc, snapshot=None, project_metadata=None):
    return FrameMetadata(
        utc_timestamp=utc,
        video_path=Path("/data/video.mov"),
        offset_s=0.0,
        sensor_snapshot=snapshot or {},
        project_metadata=project_metadata or {},
    )


T1 = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2025, 6, 1, 12, 0, 5, tzinfo=timezone.utc)


# _build_csv_row — minimal: only filename and timestamp.
def test_build_csv_row_minimal():
    meta = make_meta(T1)
    row = _build_csv_row(Path("frame_001.jpg"), meta)
    assert row == {"filename": "frame_001.jpg", "timestamp": "2025-06-01 12:00:00"}


# _build_csv_row — lat/lng included only when both are present.
def test_build_csv_row_lat_lng():
    meta = make_meta(T1, snapshot={"latitude": -32.5, "longitude": 151.2, "depth": 100.0})
    row = _build_csv_row(Path("frame_001.jpg"), meta)
    assert row["latitude"] == "-32.5"
    assert row["longitude"] == "151.2"
    assert row["depth"] == "100.0"


# _build_csv_row — full sensor snapshot produces all columns.
def test_build_csv_row_full():
    snap = {"latitude": -32.5, "longitude": 151.2, "depth": 500.0, "altitude": 3.5, "heading": 90.0}
    meta = make_meta(T1, snapshot=snap)
    row = _build_csv_row(Path("frame_001.jpg"), meta)
    assert set(row.keys()) == {"filename", "timestamp", "latitude", "longitude", "depth", "altitude", "heading"}


# write_csv_manifest — creates file in output_dir named metadata.csv.
def test_write_csv_manifest_creates_file(tmp_path):
    written = [
        (tmp_path / "frame_001.jpg", make_meta(T1)),
        (tmp_path / "frame_002.jpg", make_meta(T2)),
    ]
    result = write_csv_manifest(written, tmp_path)
    assert result == tmp_path / "metadata.csv"
    assert isinstance(result, Path)
    assert result.exists()


# write_csv_manifest — rows are sorted by timestamp regardless of input order.
def test_write_biigle_manifest_sorted(tmp_path):
    written = [
        (tmp_path / "frame_002.jpg", make_meta(T2)),
        (tmp_path / "frame_001.jpg", make_meta(T1)),
    ]
    result = write_csv_manifest(written, tmp_path)
    rows = list(csv.DictReader(result.open()))
    assert rows[0]["filename"] == "frame_001.jpg"
    assert rows[1]["filename"] == "frame_002.jpg"


# write_csv_manifest — column order follows snapshot order
def test_write_csv_manifest_column_order(tmp_path):
    snap = {"heading": 45.0, "depth": 100.0, "longitude": 151.2, "latitude": -32.5}
    written = [(tmp_path / "frame_001.jpg", make_meta(T1, snapshot=snap))]
    result = write_csv_manifest(written, tmp_path)
    with result.open() as f:
        header = f.readline().strip().split(",")
    assert header == ["filename", "timestamp", "heading", "depth", "longitude", "latitude"]



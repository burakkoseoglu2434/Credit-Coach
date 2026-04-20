from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pv
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_convert_raw_data")


def _iter_csv_inputs(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]

    if input_path.is_dir():
        return sorted(p for p in input_path.glob("*.csv") if p.is_file())

    raise FileNotFoundError(f"Input path not found: {input_path}")


def convert_csv_to_parquet(
    csv_path: Path,
    parquet_path: Path,
    *,
    overwrite: bool,
    compression: str,
    row_group_size: int,
    block_size_mb: int,
) -> None:
    if parquet_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists (use --overwrite): {parquet_path}")

    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    read_options = pv.ReadOptions(use_threads=True, block_size=int(block_size_mb) * 1024 * 1024)
    parse_options = pv.ParseOptions(delimiter=",")
    convert_options = pv.ConvertOptions(strings_can_be_null=True)

    reader = pv.open_csv(
        csv_path,
        read_options=read_options,
        parse_options=parse_options,
        convert_options=convert_options,
    )

    writer: pq.ParquetWriter | None = None
    total_rows = 0
    total_batches = 0

    try:
        for batch in reader:
            if not isinstance(batch, pa.RecordBatch):
                batch = pa.record_batch(batch)

            table = pa.Table.from_batches([batch])
            if writer is None:
                writer = pq.ParquetWriter(
                    parquet_path,
                    table.schema,
                    compression=compression,
                    use_dictionary=True,
                )
                logger.info("Schema locked from first batch: %s", csv_path.name)

            # Ensure later batches match the first-batch schema.
            if table.schema != writer.schema:
                table = table.cast(writer.schema, safe=False)

            writer.write_table(table, row_group_size=int(row_group_size))
            total_rows += int(batch.num_rows)
            total_batches += 1

    finally:
        if writer is not None:
            writer.close()

    logger.info(
        "Converted: %s -> %s (rows=%s batches=%s)",
        csv_path,
        parquet_path,
        total_rows,
        total_batches,
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert raw CSV files to Parquet for faster project runs")
    p.add_argument(
        "--input",
        type=str,
        default="data/lending_club",
        help="CSV file path or a directory containing CSVs",
    )
    p.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Optional output directory (defaults to alongside input CSV)",
    )
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing Parquet files")
    p.add_argument("--compression", type=str, default="snappy", help="Parquet compression codec")
    p.add_argument("--row_group_size", type=int, default=200_000, help="Rows per Parquet row group")
    p.add_argument(
        "--block_size_mb",
        type=int,
        default=64,
        help="CSV read block size in MB (higher can be faster but uses more memory)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(str(args.input)).expanduser()
    output_dir = Path(str(args.output_dir)).expanduser() if args.output_dir else None

    csv_paths = _iter_csv_inputs(input_path)
    if not csv_paths:
        raise FileNotFoundError(f"No .csv files found under: {input_path}")

    for csv_path in csv_paths:
        if csv_path.suffix.lower() != ".csv":
            continue
        out_dir = output_dir if output_dir else csv_path.parent
        parquet_path = out_dir / f"{csv_path.stem}.parquet"
        convert_csv_to_parquet(
            csv_path=csv_path,
            parquet_path=parquet_path,
            overwrite=bool(args.overwrite),
            compression=str(args.compression),
            row_group_size=int(args.row_group_size),
            block_size_mb=int(args.block_size_mb),
        )


if __name__ == "__main__":
    main()


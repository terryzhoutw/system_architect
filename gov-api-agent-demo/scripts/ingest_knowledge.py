"""Vectorize JSONL knowledge records and upsert them into Milvus."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rag.service import build_rag_service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=ROOT / "data" / "knowledge" / "samples",
        help="包含 JSONL 知识文件的目录",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size 必须大于 0")

    files = sorted(args.data_dir.glob("*.jsonl"))
    if not files:
        parser.error(f"目录中没有 JSONL 文件: {args.data_dir}")

    rag = build_rag_service(include_chat=False)
    total = 0
    try:
        for path in files:
            records = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            count = rag.ingest_records(records, batch_size=args.batch_size)
            total += count
            print(f"{path.name}: upserted {count} vectors")
    finally:
        rag.close()
    print(f"完成：共 upserted {total} 个向量到 Milvus 集合 {rag.store.collection_name}")


if __name__ == "__main__":
    main()

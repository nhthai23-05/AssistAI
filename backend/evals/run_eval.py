"""
Evaluate OpenAI vision model on Vietnamese receipt parsing (MC-OCR 2021).

Usage:
    python run_eval.py [--limit N] [--csv path/to/annotations.csv]

Steps:
    1. Reads .env for LLM_API_KEY, LLM_MODEL
    2. Finds annotations CSV and image folder in evals/data/
    3. Sends each receipt image to OpenAI vision API
    4. Compares extracted fields against ground truth
    5. Writes results to evals/results/eval_<timestamp>.json
"""
import argparse
import base64
import csv
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from metrics import score_prediction, aggregate

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"

EXTRACTION_PROMPT = """You are extracting key information from a Vietnamese retail receipt photo (mobile-captured, may be low quality or slightly rotated).

Vietnamese receipts use these typical field labels:
- Merchant/store name: printed prominently at the top (e.g. "MINIMART ANAN", "VinMart", "Circle K")
- Date: labeled "Ngay:", "Ngay ban:", "Ngay thanh toan:", format DD/MM/YYYY
- Total amount: labeled "Tong cong:", "Thanh tien:", "Cong:", "Tong thanh toan:", "Tong tien:", always the largest monetary value
- Amounts use period or comma as thousands separator (e.g. 74.000 or 74,000 = seventy-four thousand VND)

Return ONLY this JSON object, no explanation:
{
  "description": "<store/merchant name, string>",
  "date": "<transaction date as DD/MM/YYYY, string>",
  "amount": <total amount as plain integer, no separators, no currency symbol>,
  "category": ""
}

Rules:
- amount must be a JSON number (integer), e.g. 74000 not "74.000" or "74,000d"
- date must be DD/MM/YYYY only, strip any time or label prefix
- If a field cannot be found, use "" for strings and 0 for amount"""


def load_env() -> dict:
    env_path = Path(__file__).parent.parent / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def find_csv(data_dir: Path) -> Path | None:
    p = data_dir / "mcocr_train_df.csv"
    if p.exists():
        return p
    csvs = list(data_dir.glob("*.csv"))
    return csvs[0] if csvs else None


def find_image(data_dir: Path, img_id: str) -> Path | None:
    p = data_dir / "train_images" / img_id
    if p.exists():
        return p
    # Fallback: recursive search
    for found in data_dir.rglob(img_id):
        return found
    return None


import re as _re

def extract_ground_truth(row: dict) -> dict:
    """
    Convert MC-OCR annotation row to {description, date, amount, category} schema.
    anno_labels/anno_texts are ||| separated:
      SELLER|||ADDRESS|||TIMESTAMP|||TOTAL_COST
      Cua hang ABC|||123 Le Loi|||Ngay : 15/03/2021 10:30|||150.000
    """
    raw = {"seller": "", "timestamp": "", "total_cost": ""}
    labels = [l.strip() for l in str(row.get("anno_labels", "")).split("|||")]
    texts  = [t.strip() for t in str(row.get("anno_texts",  "")).split("|||")]
    for lbl, txt in zip(labels, texts):
        key = lbl.upper()
        if key == "SELLER"      and not raw["seller"]:    raw["seller"]     = txt
        elif key == "TIMESTAMP" and not raw["timestamp"]: raw["timestamp"]  = txt
        elif key == "TOTAL_COST" and _re.search(r"\d", txt):
            raw["total_cost"] = txt  # keep last numeric occurrence

    # Parse date: extract DD/MM/YYYY from timestamp string
    date_match = _re.search(r"\d{1,2}/\d{1,2}/\d{4}", raw["timestamp"])
    date = date_match.group(0) if date_match else ""

    # Parse amount: strip all non-digits
    digits = _re.sub(r"[^\d]", "", raw["total_cost"])
    amount = int(digits) if digits else 0

    return {
        "description": raw["seller"],
        "date":        date,
        "amount":      amount,
        "category":    "",
    }


def call_openai_vision(client, model: str, image_path: Path) -> dict:
    """Send image to OpenAI vision and return extracted fields dict."""
    image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    ext = image_path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text",      "text": EXTRACTION_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}},
            ],
        }],
        max_completion_tokens=300,
        temperature=0,
    )
    content = response.choices[0].message.content or ""
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"description": "", "date": "", "amount": 0, "category": "", "_raw": content}


def run(limit: int | None = None, csv_path: Path | None = None):
    env = load_env()
    api_key = env.get("LLM_API_KEY", "")
    model   = env.get("LLM_MODEL", "gpt-4o-mini")

    if not api_key:
        print("ERROR: LLM_API_KEY not set in .env")
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    csv_file = csv_path or find_csv(DATA_DIR)
    if not csv_file:
        print(f"ERROR: No CSV annotation file found in {DATA_DIR}")
        print("Run: python download_dataset.py")
        sys.exit(1)

    print(f"Model  : {model}")
    print(f"CSV    : {csv_file}")
    print(f"Limit  : {limit or 'all'}")
    print()

    # Group rows by img_id (dataset may have one row per text-line)
    rows_by_img: dict[str, list] = {}
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img_id = row.get("img_id", row.get("image_id", ""))
            if img_id:
                rows_by_img.setdefault(img_id, []).append(row)

    all_ids = list(rows_by_img.keys())
    random.seed(42)
    random.shuffle(all_ids)
    img_ids = all_ids[: (limit if limit is not None else 100)]

    all_scores = []
    errors = []

    for i, img_id in enumerate(img_ids, 1):
        image_path = find_image(DATA_DIR, img_id)
        if not image_path:
            print(f"[{i}/{len(img_ids)}] SKIP  {img_id} — image not found")
            errors.append({"img_id": img_id, "error": "image not found"})
            continue

        # Merge ground truth from all rows for this image
        gt = {"description": "", "date": "", "amount": 0, "category": ""}
        for row in rows_by_img[img_id]:
            partial = extract_ground_truth(row)
            for k in gt:
                if not gt[k] and partial[k]:
                    gt[k] = partial[k]

        try:
            pred = call_openai_vision(client, model, image_path)
            score = score_prediction(pred, gt)
            score["img_id"] = img_id
            all_scores.append(score)
            status = "OK" if score["avg_f1"] >= 0.8 else "~" if score["avg_f1"] >= 0.4 else "X"
            print(f"[{i}/{len(img_ids)}] {status}  {img_id}  f1={score['avg_f1']:.2f}  "
                  f"desc={score['description']['f1']:.2f}  "
                  f"amount={score['amount']['exact']}")
        except Exception as e:
            print(f"[{i}/{len(img_ids)}] ERROR {img_id}: {e}")
            errors.append({"img_id": img_id, "error": str(e)})
            time.sleep(1)

        time.sleep(0.3)

    agg = aggregate(all_scores)
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"eval_{ts}.json"
    out_path.write_text(json.dumps({
        "model": model,
        "n_evaluated": len(all_scores),
        "n_errors": len(errors),
        "aggregate": agg,
        "samples": all_scores,
        "errors": errors,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=" * 50)
    print(f"Model          : {model}")
    print(f"Evaluated      : {len(all_scores)} / {len(img_ids)}")
    if agg:
        print(f"Overall avg F1 : {agg.get('overall_avg_f1', 0):.3f}")
        for field in ("description", "date", "amount"):
            f = agg.get(field, {})
            print(f"  {field:<12}: exact={f.get('exact_acc',0):.3f}  f1={f.get('avg_f1',0):.3f}")
    print(f"Results saved  : {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Max images to evaluate")
    parser.add_argument("--csv",   type=str, default=None, help="Path to annotations CSV")
    args = parser.parse_args()
    run(limit=args.limit, csv_path=Path(args.csv) if args.csv else None)

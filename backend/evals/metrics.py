"""Evaluation metrics for receipt field extraction.

Schema: {description, date, amount, category}
  - description : store/merchant name (string)
  - date        : DD/MM/YYYY (string)
  - amount      : integer VND, no separators
  - category    : not evaluated (not in ground truth)
"""
import re


def normalize_str(text: str) -> str:
    """Lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def normalize_amount(value) -> int | None:
    """Coerce amount to integer (strips non-digits from strings, rounds floats)."""
    if isinstance(value, (int, float)):
        return int(round(value))
    digits = re.sub(r"[^\d]", "", str(value or ""))
    return int(digits) if digits else None


def char_f1(pred: str, gt: str) -> float:
    """Character-level F1."""
    p = list(normalize_str(pred))
    g = list(normalize_str(gt))
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    common = sum(min(p.count(c), g.count(c)) for c in set(g))
    prec = common / len(p)
    rec  = common / len(g)
    return 2 * prec * rec / (prec + rec) if prec + rec else 0.0


def amount_exact(pred, gt, tolerance: float = 0.01) -> bool:
    """True if amounts are within 1% of each other."""
    p, g = normalize_amount(pred), normalize_amount(gt)
    if p is None or g is None:
        return False
    if g == 0:
        return p == 0
    return abs(p - g) / g <= tolerance


def date_exact(pred: str, gt: str) -> bool:
    """Exact match after normalising DD/MM/YYYY."""
    def _norm(s: str) -> str:
        m = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", str(s or ""))
        if not m:
            return s.strip().lower()
        d, mo, y = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
        return f"{d}/{mo}/{y}"
    return _norm(pred) == _norm(gt)


def score_prediction(pred: dict, gt: dict) -> dict:
    """
    Score one prediction against ground truth.
    pred/gt keys: description, date, amount, category
    """
    result = {
        "description": {
            "pred":  pred.get("description", ""),
            "gt":    gt.get("description", ""),
            "exact": normalize_str(pred.get("description", "")) == normalize_str(gt.get("description", "")),
            "f1":    char_f1(pred.get("description", ""), gt.get("description", "")),
        },
        "date": {
            "pred":  pred.get("date", ""),
            "gt":    gt.get("date", ""),
            "exact": date_exact(pred.get("date", ""), gt.get("date", "")),
            "f1":    char_f1(pred.get("date", ""), gt.get("date", "")),
        },
        "amount": {
            "pred":  pred.get("amount", 0),
            "gt":    gt.get("amount", 0),
            "exact": amount_exact(pred.get("amount", 0), gt.get("amount", 0)),
            "f1":    1.0 if amount_exact(pred.get("amount", 0), gt.get("amount", 0)) else 0.0,
        },
    }
    result["avg_f1"] = sum(result[f]["f1"] for f in ("description", "date", "amount")) / 3
    return result


def aggregate(scores: list) -> dict:
    """Aggregate per-sample scores into dataset-level metrics."""
    if not scores:
        return {}
    fields = ("description", "date", "amount")
    out = {}
    for field in fields:
        fs = [s[field] for s in scores if field in s]
        out[field] = {
            "exact_acc": sum(s["exact"] for s in fs) / len(fs),
            "avg_f1":    sum(s["f1"]    for s in fs) / len(fs),
            "n": len(fs),
        }
    out["overall_avg_f1"] = sum(out[f]["avg_f1"] for f in fields) / len(fields)
    return out

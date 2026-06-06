"""Download Vietnamese Receipts MC-OCR 2021 dataset from Kaggle."""
import os
import sys
import json
import shutil
import zipfile
from pathlib import Path

# Files/dirs to keep after extraction (everything else is deleted)
_KEEP = {"mcocr_train_df.csv", "train_images"}

DATASET_SLUG = "domixi1989/vietnamese-receipts-mc-ocr-2021"
DATA_DIR = Path(__file__).parent / "data"


def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def setup_kaggle_auth(env: dict):
    """Set up Kaggle credentials from env token."""
    token = env.get("KAGGLE_API_TOKEN", "")
    if not token:
        print("ERROR: KAGGLE_API_TOKEN not set in .env")
        sys.exit(1)

    kaggle_dir = Path.home() / ".kaggle"
    kaggle_dir.mkdir(exist_ok=True)
    kaggle_json = kaggle_dir / "kaggle.json"

    # New-style KGAT bearer token — write to ~/.kaggle/access_token
    if token.startswith("KGAT_"):
        os.environ["KAGGLE_API_TOKEN"] = token
        access_token_file = kaggle_dir / "access_token"
        access_token_file.write_text(token, encoding="utf-8")
        try:
            import stat
            access_token_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
    else:
        # Legacy username:key pair
        if ":" in token:
            username, key = token.split(":", 1)
        else:
            print("ERROR: KAGGLE_API_TOKEN must be KGAT_xxx or username:key")
            sys.exit(1)
        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"] = key
        kaggle_json.write_text(json.dumps({"username": username, "key": key}), encoding="utf-8")
        try:
            import stat
            kaggle_json.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass


def _cleanup(data_dir: Path):
    """Remove everything except _KEEP, then flatten nested train_images."""
    for p in list(data_dir.iterdir()):
        if p.name not in _KEEP:
            shutil.rmtree(p) if p.is_dir() else p.unlink()

    # Flatten train_images/train_images -> train_images
    nested = data_dir / "train_images" / "train_images"
    if nested.exists():
        for f in nested.iterdir():
            f.rename(data_dir / "train_images" / f.name)
        nested.rmdir()


def download():
    env = load_env()
    setup_kaggle_auth(env)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if any(DATA_DIR.glob("*.csv")):
        print(f"Dataset already extracted at {DATA_DIR}")
        return

    print(f"Downloading {DATASET_SLUG} ...")
    import kaggle
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(DATASET_SLUG, path=str(DATA_DIR), unzip=False)

    zips = list(DATA_DIR.glob("*.zip"))
    if not zips:
        print("ERROR: No zip file downloaded")
        sys.exit(1)
    zip_path = zips[0]

    print(f"Extracting {zip_path.name} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(DATA_DIR)
    zip_path.unlink()

    _cleanup(DATA_DIR)

    print("Done. Kept:")
    for p in sorted(DATA_DIR.iterdir()):
        if p.is_dir():
            n = sum(1 for _ in p.rglob("*") if _.is_file())
            print(f"  {p.name}/ ({n} files)")
        else:
            print(f"  {p.name}")


if __name__ == "__main__":
    download()

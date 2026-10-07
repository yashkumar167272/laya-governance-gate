import os

# Disable Xet BEFORE importing huggingface_hub so it takes effect
os.environ["HF_HUB_DISABLE_XET"] = "1"

from huggingface_hub import snapshot_download

repo_id = "convaiinnovations/laya"
local_dir = "./laya_base_model"

print(f"Downloading {repo_id} to {local_dir} ...")

path = snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
    local_dir_use_symlinks=False,   # save real files, not symlinks
    resume_download=True,           # pick up where the earlier attempt left off
    max_workers=2,                  # fewer parallel workers = more stable on Windows
)

print(f"\n✅ Download complete. Files saved to: {path}")
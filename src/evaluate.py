import csv
import json
import os
import matplotlib

matplotlib.use("Agg")  # headless-safe; we only save files, never show
import matplotlib.pyplot as plt


DECISIONS_PATH = "outputs/decisions.jsonl"
LABELS_PATH = "data/labels.csv"
PLOT_PATH = "outputs/reliability.png"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_decisions(path=DECISIONS_PATH):
    """Read one JSON object per line into a dict keyed by change_id."""
    decisions = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            decisions[obj["change_id"]] = obj
    return decisions


def load_labels(path=LABELS_PATH):
    """Read the CSV into a dict keyed by change_id."""
    labels = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels[row["change_id"]] = row
    return labels


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def confusion_matrix(pairs):
    """
    pairs: list of (laya_answer, label) tuples for should_allow.
    Returns a dict of counts for the 4 cells.
    """
    cells = {
        ("yes", "yes"): 0,
        ("yes", "no"): 0,
        ("no", "yes"): 0,
        ("no", "no"): 0,
    }
    for laya, label in pairs:
        if (laya, label) in cells:
            cells[(laya, label)] += 1
    return cells


def print_confusion(cells, total):
    print("Confusion matrix for should_allow")
    print("  rows = Laya, cols = your label")
    print()
    print("                 label_yes   label_no")
    print(f"  Laya_yes       {cells[('yes','yes')]:^9}   {cells[('yes','no')]:^8}")
    print(f"  Laya_no        {cells[('no','yes')]:^9}   {cells[('no','no')]:^8}")
    print()
    print(f"  total rows: {total}")


def agreement_rate(pairs):
    if not pairs:
        return 0.0
    correct = sum(1 for laya, label in pairs if laya == label)
    return correct / len(pairs)


def mean_absolute_error(risk_pairs):
    """
    risk_pairs: list of (laya_float, label_int).
    """
    if not risk_pairs:
        return 0.0
    total = 0.0
    for laya, label in risk_pairs:
        total += abs(laya - label)
    return total / len(risk_pairs)


# ---------------------------------------------------------------------------
# Reliability diagram
# ---------------------------------------------------------------------------

def reliability_points(conf_pairs, n_bins=10):
    """
    conf_pairs: list of (confidence, is_correct).
    Returns list of (bin_center, agreement_fraction) for non-empty bins.
    """
    bins = [[] for _ in range(n_bins)]
    for conf, correct in conf_pairs:
        # Clamp to [0,1] just in case
        c = min(max(conf, 0.0), 1.0)
        # Last bin includes 1.0
        idx = int(c * n_bins)
        if idx == n_bins:
            idx = n_bins - 1
        bins[idx].append(correct)

    points = []
    for i, bucket in enumerate(bins):
        if not bucket:
            continue
        center = (i + 0.5) / n_bins
        frac = sum(bucket) / len(bucket)
        points.append((center, frac))
    return points


def plot_reliability(points, path=PLOT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 6))

    # Diagonal reference
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="perfect calibration")

    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.plot(xs, ys, marker="o", color="tab:blue", label="Laya")

    ax.set_xlabel("Laya's confidence")
    ax.set_ylabel("observed agreement")
    ax.set_title("Reliability diagram — should_allow")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\nSaved reliability diagram to {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    decisions = load_decisions()
    labels = load_labels()

    # Join on change_id
    common = sorted(set(decisions) & set(labels))
    only_dec = sorted(set(decisions) - set(labels))
    only_lab = sorted(set(labels) - set(decisions))

    if only_dec:
        print(f"WARNING: decisions without labels: {only_dec}")
    if only_lab:
        print(f"WARNING: labels without decisions: {only_lab}")

    print(f"Joined {len(common)} rows.\n")

    # Build pair lists
    allow_pairs = []      # (laya_answer, label)
    allow_conf_pairs = [] # (confidence, is_correct)
    risk_pairs = []       # (laya_float, label_int)
    review_pairs = []     # (laya_answer, label)

    for cid in common:
        d = decisions[cid]
        l = labels[cid]

        laya_allow = d["should_allow"]["answer"]
        laya_allow_conf = float(d["should_allow"]["confidence"])
        label_allow = l["should_allow"]

        allow_pairs.append((laya_allow, label_allow))
        allow_conf_pairs.append((laya_allow_conf, 1 if laya_allow == label_allow else 0))

        laya_risk = float(d["risk_level"]["answer"])
        label_risk = int(l["risk_level"])
        risk_pairs.append((laya_risk, label_risk))

        laya_review = d["needs_review"]["answer"]
        label_review = l["needs_review"]
        review_pairs.append((laya_review, label_review))

    # Metrics
    cells = confusion_matrix(allow_pairs)
    print_confusion(cells, len(allow_pairs))

    print()
    print(f"should_allow agreement:  {agreement_rate(allow_pairs):.3f}")
    print(f"needs_review agreement:  {agreement_rate(review_pairs):.3f}")
    print(f"risk_level MAE:          {mean_absolute_error(risk_pairs):.3f}")

    # Reliability
    points = reliability_points(allow_conf_pairs, n_bins=10)
    print("\nReliability points (bin_center, agreement):")
    for c, f in points:
        print(f"  {c:.2f}  ->  {f:.2f}")

    plot_reliability(points)


if __name__ == "__main__":
    main()
import json
import os

import laya

from load import load_catalog, load_lineage, load_changes
from state import build_all_states


MODEL_PATH = "./laya_base_model"
OUTPUT_PATH = "outputs/decisions.jsonl"


QUESTIONS = {
    "should_allow": {
        "type": "choice",
        "instructions": "Should this schema change be allowed?",
        "criteria": {
            "yes": "The change is safe and should be approved",
            "no": "The change poses unacceptable risk and should be blocked"
        }
    },
    "risk_level": {
        "type": "score",
        "instructions": "How risky is this change on a 1 to 5 scale?",
        "criteria": [
            "minimal risk, no meaningful impact",
            "low risk, minor and contained",
            "moderate risk, requires attention",
            "high risk, significant downstream impact",
            "critical risk, likely to cause breakage"
        ]
    },
    "needs_review": {
        "type": "choice",
        "instructions": "Does this change require human review before proceeding?",
        "criteria": {
            "yes": "A human should review this change",
            "no": "This change can proceed without human review"
        }
    }
}


def decide(state, agent):
    result = agent.predict(state, QUESTIONS)
    answers = result["answers"]

    return {
        "change_id": state["change_id"],
        "should_allow": {
            "answer": answers["should_allow"]["choice"],
            "confidence": answers["should_allow"]["answer_confidence"],
        },
        "risk_level": {
            "answer": answers["risk_level"]["score"],
            "confidence": answers["risk_level"]["answer_confidence"],
        },
        "needs_review": {
            "answer": answers["needs_review"]["choice"],
            "confidence": answers["needs_review"]["answer_confidence"],
        },
    }


def run_all(states, agent, output_path=OUTPUT_PATH):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    decisions = []
    for state in states:
        cid = state["change_id"]
        try:
            decision = decide(state, agent)
            decisions.append(decision)
            sa = decision["should_allow"]["answer"]
            rl = decision["risk_level"]["answer"]
            nr = decision["needs_review"]["answer"]
            print(f"{cid} done (should_allow={sa}, risk={rl}, review={nr})")
        except Exception as e:
            print(f"{cid} FAILED: {e}")

    decisions.sort(key=lambda d: d["change_id"])

    with open(output_path, "w", encoding="utf-8") as f:
        for d in decisions:
            f.write(json.dumps(d) + "\n")

    print(f"\nWrote {len(decisions)} decisions to {output_path}")
    return decisions


def main():
    print("Loading data...")
    catalog = load_catalog()
    lineage = load_lineage()
    changes = load_changes()
    states = build_all_states(changes, catalog, lineage)
    print(f"Built {len(states)} states.\n")

    print("Loading Laya...")
    agent = laya.load(MODEL_PATH)
    print("Model loaded.\n")

    print("Running decisions...")
    run_all(states, agent)


if __name__ == "__main__":
    main()
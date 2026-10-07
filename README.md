
---

## Three things to change before you commit this

1. **The download step.** Your README says `python download_laya.py`, but you do not have that file — you downloaded Laya with an inline script. Either save that script as `download_laya.py` and commit it, or rewrite that section of the README to describe the manual `snapshot_download` call. A README that references a missing file looks careless.

2. **The exact numbers.** I used the numbers from your evaluation run (0.20, 0.533, 1.025, and the reliability bins). Confirm they match `outputs/decisions.jsonl` and the printed output exactly. Do not round differently in the README than the script prints.

3. **The tone.** Right now the README is honest and specific. Resist the urge to add marketing language like "powerful" or "state-of-the-art." The results section is stronger because it does not oversell. Keep it that way.

---

## After the README

- Add a `requirements.txt` with the pinned versions (`laya`, `torch`, `transformers`, `matplotlib`).
- Make sure `.gitignore` excludes `.venv/`, `outputs/`, `laya_base_model/`, and `__pycache__/`. The model folder is hundreds of megabytes and should never be committed.
- Optionally add a screenshot of the reliability diagram to the README with `![reliability](outputs/reliability.png)`.
- Commit and push.

Then paste the README back here and I will do one review pass — mostly checking the numbers match, the tone is right, and the "what I would do next" section sounds like an engineer rather than a student.
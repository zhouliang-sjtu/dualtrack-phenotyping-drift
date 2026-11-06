# -*- coding: utf-8 -*-
r"""llm_extraction_external_site.py —— external site 外部验证：LLM 轨零调参批处理（不读任何人工标注）

manifest（extractor_manifest.json）：
  ECG : prompt v1  sha16=dbb1ebe717ad3497  （docs/prompts/llm_ecg_prompt_template_v1.md）
  ABD : prompt v2.1b sha16=bcdc6563420538bb（同目录 llm_abd_prompt_template_v2.md，flags-only 输出）
运行：Ollama 本地 http://127.0.0.1:11434/v1/chat/completions；qwen2.5:14b；temperature=0；seed=42
      max_tokens：ECG 400（沿用既有运行配置）、ABD 300（沿用既有运行配置）
输入：data/external_site/analysis_corpus.csv（text 已掩码）
输出：data/external_site/
      external_site_llm_ecg.csv  (sample_id, input_hash, llm_raw, output_hash, prompt_sha16, input_sha256)
      external_site_llm_abdomen.csv
断点续跑：以 input_hash 为键；prompt_sha16 不一致则弃用旧输出重跑。

随包落位：本脚本位于 code/extraction/；掩码语料与两轨原始输出位于 data/external_site/；
      prompt 指纹登记于 extractor_manifest.json。
"""
import argparse
import hashlib
import os
import sys
import time

import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STUDY = os.path.dirname(ROOT)
OUTDIR = os.path.join(STUDY, "data", "external_site")
CORPUS = os.path.join(STUDY, "data", "external_site", "analysis_corpus.csv")
PROMPT_DIR = os.path.join(STUDY, "docs", "prompts")
ENDPOINT = "http://127.0.0.1:11434/v1/chat/completions"
MODEL = "qwen2.5:14b"
TEMP, SEED = 0.0, 42

TASKS = {
    "ECG": {"prompt": "llm_ecg_prompt_template_v1.md", "expected_sha": "dbb1ebe717ad3497",
            "max_tokens": 400, "out": "external_site_llm_ecg.csv"},
    "ABD": {"prompt": "llm_abd_prompt_template_v2.md", "expected_sha": "bcdc6563420538bb",
            "max_tokens": 300, "out": "external_site_llm_abdomen.csv"},
}


def sha(s):
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:16]


def sha_full(s):
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()


def run_domain(dom, cfg, C, limit=None):
    pf = os.path.join(PROMPT_DIR, cfg["prompt"])
    system = open(pf, encoding="utf-8").read()
    psha = sha(system)
    print(f"\n[{dom}] prompt={cfg['prompt']} sha16={psha} "
          f"{'OK' if psha == cfg['expected_sha'] else '!!! 与 manifest 不一致'}", flush=True)
    if psha != cfg["expected_sha"]:
        raise SystemExit("prompt sha 与 manifest 登记不一致，停止批处理")

    df = C[C.domain == dom].copy()
    if limit:
        df = df.head(limit)
    out = os.path.join(OUTDIR, cfg["out"])
    done = {}
    if os.path.exists(out):
        prev = pd.read_csv(out, encoding="utf-8-sig", dtype=str).fillna("")
        if len(prev) and str(prev.iloc[0].get("prompt_sha16", "")) == psha:
            done = dict(zip(prev["input_hash"], prev["llm_raw"]))
            print(f"  续跑：已有 {len(done)} 条（prompt sha 校验通过）", flush=True)
        else:
            print("  prompt sha 变化，弃用旧输出", flush=True)

    sess = requests.Session()
    rows, t0 = [], time.time()
    for i, r in enumerate(df.itertuples(index=False)):
        text = str(r.text)
        ih = sha_full(text)
        if ih in done:
            rows.append({"sample_id": r.sample_id, "input_hash": ih, "llm_raw": done[ih],
                         "output_hash": sha_full(done[ih]), "prompt_sha16": psha})
            continue
        resp, err = None, ""
        for attempt in range(3):
            try:
                payload = {"model": MODEL, "temperature": TEMP, "seed": SEED,
                           "max_tokens": cfg["max_tokens"],
                           "messages": [{"role": "system", "content": system},
                                        {"role": "user", "content": text}]}
                resp = sess.post(ENDPOINT, json=payload, timeout=600).json()["choices"][0]["message"]["content"]
                break
            except Exception as e:  # noqa: BLE001
                err = str(e)
                print(f"  retry {r.sample_id}: {e}", flush=True)
                time.sleep(2 ** attempt)
        rows.append({"sample_id": r.sample_id, "input_hash": ih,
                     "llm_raw": resp if resp is not None else "ERROR",
                     "output_hash": sha_full(resp) if resp is not None else "",
                     "prompt_sha16": psha, "error": err})
        if (i + 1) % 10 == 0:
            pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
            el = time.time() - t0
            print(f"  {dom} {i+1}/{len(df)} elapsed={el:.0f}s eta={el/(i+1)*(len(df)-i-1):.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    nerr = sum(1 for x in rows if x["llm_raw"] == "ERROR")
    print(f"[{dom}] 完成 {len(rows)} 条 ERROR={nerr} 用时 {time.time()-t0:.0f}s -> {cfg['out']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="ECG,ABD")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    C = pd.read_csv(CORPUS, encoding="utf-8-sig", dtype=str).fillna("")
    print(f"语料 {CORPUS} | {C.shape}")
    for dom in [x.strip() for x in a.domain.split(",") if x.strip()]:
        run_domain(dom, TASKS[dom], C, a.limit or None)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""make_version_contrast_inputs.py —— 生成 production-freeze variant（一次性工具）＋ 与本包随附件核对

（2026-11-05）整改：旧版以「代码改写代码」把**硬编码绝对路径** CACHE
注入生成件（形式可溯源、实质不可溯源，且注入值随机房而变）。新版改为：
  1) 生成件 CACHE 行参数化 —— os.environ.get("VERSION_CONTRAST_CACHE", os.path.join(RES, ...))：
     默认落 results/（缓存缺失时走现场重算分支，语义同原版），设 VERSION_CONTRAST_CACHE 可指回
     baseline 文本结局缓存复用（A0 论证不变：文本域在 production freeze 未变，缓存有效）。
  2) 本脚本对上游原件只施加**唯一记录在案的变换**（头注两行 + CACHE/RES/sys.path 三行），其余逐字保留；
     并默认与本包随附件（code/wp1/version_contrast_run.py）做 unified
     diff 核对 —— 差异必须为 0 行，核对报告落 results/verify 目录（不进入发布包）。
用法：
  python make_version_contrast_inputs.py                 # 校验模式（默认）：与本包随附件 diff，差异=0 则 PASS
  python make_version_contrast_inputs.py --out PATH      # 另存生成件（不写包内）
  --src 指定上游原件（默认 code/ 下的 baseline 原版）
"""
import argparse
import difflib
import io
import os
import sys

ROOT = r"STUDY_ROOT"
SCRIPT_DIR = os.path.join(ROOT, "code", "wp1")
EVID = os.path.join(ROOT, "results", "verify")

OLD_LINE = 'CACHE = os.path.join(RES, "outcome_cache_v3.csv.gz")'
OLD_RES = 'RES = os.path.join(ROOT, "results")'
NEW_LINE = ('CACHE = os.environ.get("VERSION_CONTRAST_CACHE", os.path.join(RES, "outcome_cache_v3.csv.gz"))  '
            '# baseline 文本结局缓存可经 VERSION_CONTRAST_CACHE 指回复用（the text domain is unchanged in the production freeze, so the cache remains valid）')
NEW_RES = ('RES = os.environ.get("VERSION_CONTRAST_RES", os.path.join(ROOT, "results"))'
           '  # VERSION_CONTRAST_RES: output directory overridable')
OLD_SYS = ('    sys.path.insert(0, os.path.join(ROOT, "code"))\n'
           '    from main import extract_ecg, norm')
NEW_SYS = ('    sys.path.insert(0, os.path.join(ROOT, "code")); '
           'sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  '
           '# deposited main.py in this package takes precedence\n'
           '    from main import extract_ecg, norm')
HDR = ("# production-freeze variant（2026-09-21）：本文件位于 code/wp1/，"
       "ROOT 解析到本包 → 全部输出落 results/，\n"
       "# 不触碰原 study results（baseline 留档）。唯一改动 = CACHE 行参数化（VERSION_CONTRAST_CACHE 环境变量覆盖；"
       "默认 results/，可指回 baseline 缓存复用——the text domain is unchanged in the production freeze, so the cache remains valid）与 RES 输出目录参数化"
       "（VERSION_CONTRAST_RES 环境变量覆盖；默认 results/）。\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.path.join(ROOT, "code", "version_contrast_equivalence.py"),
                    help='上游 baseline 原件（包外，历史布局）')
    ap.add_argument('--deployed', default=os.path.join(SCRIPT_DIR, "version_contrast_run.py"),
                    help='本包随附件（核对对象）')
    ap.add_argument('--out', default=None, help='另存生成件；缺省仅校验')
    a = ap.parse_args()

    src = io.open(a.src, encoding="utf-8").read()
    assert src.count(OLD_LINE) == 1, "上游原件 CACHE 行未唯一命中"
    assert src.count(OLD_RES) == 1, "上游原件 RES 行未唯一命中"
    assert src.count(OLD_SYS) == 1, "上游原件 sys.path 两行未唯一命中"
    generated = (HDR + src.replace(OLD_LINE, NEW_LINE, 1).replace(OLD_RES, NEW_RES, 1)
                 .replace(OLD_SYS, NEW_SYS, 1))

    deployed = io.open(a.deployed, encoding="utf-8").read()
    diff = list(difflib.unified_diff(
        deployed.splitlines(), generated.splitlines(),
        fromfile='deployed(version_contrast_run.py)', tofile='generated(make_version_contrast_inputs)', lineterm=''))
    report = ["=== make_version_contrast_inputs verify ===",
              f"src={a.src}", f"deployed={a.deployed}",
              f"diff_lines={len(diff)}", ""] + diff
    os.makedirs(EVID, exist_ok=True)
    io.open(os.path.join(EVID, "version_contrast_diff.txt"), "w", encoding="utf-8").write(
        "\n".join(report) + "\n")
    if a.out:
        io.open(a.out, "w", encoding="utf-8").write(generated)
        print("generated copy written:", a.out)
    if diff:
        print("\n".join(diff))
        sys.exit("FAIL: 本包随附件与唯一记录在案的变换不一致（in-package deployment check failed）")
    print("VERIFY PASS: deployed == generated（差异 0 行；唯一变换 = CACHE/RES/sys.path 行参数化 + 头注）")


if __name__ == "__main__":
    main()

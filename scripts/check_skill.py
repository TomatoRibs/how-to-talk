#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill 包级规范校验。20 条规则，S01–S20。

检查的是「这个包作为一个交付物合不合格」，不是「某条消息说得好不好」。
后者由 check_message.py 负责。

用法：
    python3 check_skill.py <技能目录>
    python3 check_skill.py <技能目录> --strict   # WARN 也当失败
    python3 check_skill.py --list                # 只列规则
    python3 check_skill.py <技能目录> --json      # 机器可读

不传目录时，默认校验脚本所在包（脚本上级目录）。

退出码：0 全过（或只有 WARN），1 有 FAIL（--strict 时 WARN 也算）。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FAIL, WARN, OK = "FAIL", "WARN", "OK"

# metadata 里必须有值的字段。缺一个，这个包就被当成「半成品」
REQUIRED_META = ["author", "version", "category", "license", "created"]

# 目录里不许出现的东西。运行时数据属于使用者，不属于 skill 包
FORBIDDEN_DIRS = ["state", "node_modules", "__pycache__", ".git", ".venv"]

# 一个文件少于这么多行，基本等于占位符
DEFAULT_MIN_LINES = 30

RULES = [
    ("S01", "SKILL.md 与 frontmatter 成对存在"),
    ("S02", "frontmatter name 等于目录名"),
    ("S03", "description 有长度、有触发词、有不适用"),
    ("S04", "metadata 必填字段齐全"),
    ("S05", "license 声明配得上 LICENSE 文件"),
    ("S06", "点名的 reference / 脚本 / assets 全部存在"),
    ("S07", "references 编号连续，不跳号"),
    ("S08", "无孤儿参考文件"),
    ("S09", "assets 引用完整"),
    ("S10", "版本三处一致（frontmatter / 正文 / CHANGELOG）"),
    ("S11", "CHANGELOG 每条有日期、从新到旧"),
    ("S12", "无 TODO / 待补 / 占位标记"),
    ("S13", "包内不放运行时数据"),
    ("S14", "无过薄文件"),
    ("S15", "check_message.py 自测通过"),
    ("S16", "references 无已废除的旧口径"),
    ("S17", "样本消息通过 check_message（条款与示例绑定）"),
    ("S18", "SKILL.md 有加载策略（什么时候读哪个文件）"),
    ("S19", "SKILL.md 有明确流程（第 N 步 / 流水线）"),
    ("S20", "SKILL.md 有诚实边界（做不到什么）"),
]


class Ctx:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.results = []
        self.cfg = self._load_cfg()

    def _load_cfg(self):
        p = self.root / ".clone2.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    @property
    def skill_md(self):
        return self.root / "SKILL.md"

    def read(self, p):
        try:
            return Path(p).read_text(encoding="utf-8")
        except Exception:
            return ""

    def add(self, level, code, msg):
        self.results.append((level, code, msg))

    def counts(self):
        c = {FAIL: 0, WARN: 0, OK: 0}
        for lv, _, _ in self.results:
            c[lv] += 1
        return c


# ── 工具 ─────────────────────────────────────────────────────

def parse_frontmatter(text):
    """不依赖 pyyaml，手写解析。只认顶层 key 和 metadata 下的 key。"""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, None
    block = m.group(1)
    top, meta = {}, {}
    in_meta = False
    cur_key = None
    for line in block.split("\n"):
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        s = line.strip()
        if s.startswith("metadata:"):
            in_meta = True
            continue
        if indent == 0 and ":" in s:
            in_meta = False
            k, v = s.split(":", 1)
            top[k.strip()] = v.strip().strip('"').strip("'")
            cur_key = k.strip()
        elif in_meta and indent > 0 and ":" in s:
            k, v = s.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
        elif indent > 0 and cur_key:
            top[cur_key] = (top.get(cur_key, "") + " " + s).strip()
    return top, meta


# ── 各项检查 ─────────────────────────────────────────────────

def check_structure(c: Ctx):
    if not c.skill_md.exists():
        c.add(FAIL, "S01", "SKILL.md 不存在")
        return None, None
    text = c.read(c.skill_md)
    top, meta = parse_frontmatter(text)
    if top is None:
        c.add(FAIL, "S01", "SKILL.md 开头没有成对的 --- frontmatter")
        return text, None
    c.add(OK, "S01", "SKILL.md 与 frontmatter 齐全")

    name = top.get("name", "")
    if name != c.root.name:
        c.add(FAIL, "S02", f"frontmatter name「{name}」≠ 目录名「{c.root.name}」")
    else:
        c.add(OK, "S02", f"name 与目录名一致（{name}）")

    desc = top.get("description", "")
    lacks = []
    if len(desc) < 100:
        lacks.append(f"只有 {len(desc)} 字")
    if "触发" not in desc and "trigger" not in desc.lower():
        lacks.append("没写触发词")
    if "不适用" not in desc and "not for" not in desc.lower():
        lacks.append("没写不适用")
    if len(desc) < 100:
        c.add(FAIL, "S03", f"description {'、'.join(lacks)}。它是唯一的分发入口，写短等于没写")
    elif lacks:
        c.add(WARN, "S03", f"description {'、'.join(lacks)}")
    else:
        c.add(OK, "S03", f"description {len(desc)} 字，触发词与不适用齐全")

    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        c.add(FAIL, "S04", f"metadata 缺 {missing}")
    else:
        c.add(OK, "S04", f"metadata {len(REQUIRED_META)} 个必填字段齐全，version={meta['version']}")

    return text, meta


def check_license(c: Ctx, meta):
    if not meta or meta.get("license") != "MIT":
        c.add(WARN, "S05", "license 字段不是 MIT，跳过配文件检查")
        return
    p = c.root / "LICENSE"
    if not p.exists():
        c.add(FAIL, "S05", "metadata 声明 MIT，但目录里没有 LICENSE 文件")
        return
    body = c.read(p)
    if "MIT License" not in body or len(body) < 400:
        c.add(FAIL, "S05", "LICENSE 存在但内容不完整")
    else:
        c.add(OK, "S05", "LICENSE 与 license 字段一致")


def check_references(c: Ctx, text):
    """SKILL.md 里点名的文件必须真的存在；存在但没被点名的，是孤儿。"""
    refs_named = set(re.findall(r"`?references/([0-9]{2}-[A-Za-z0-9_\-\u4e00-\u9fff]+\.md)`?", text))
    scripts_named = set(re.findall(r"`?(?:scripts/)?([a-z_]+\.py)`?", text))
    assets_named = set(re.findall(r"`?assets/([^`）)\s]+)`?", text))

    bad = []
    for f in sorted(refs_named):
        if not (c.root / "references" / f).exists():
            bad.append(f"references/{f}")
    for f in sorted(scripts_named):
        if not (c.root / "scripts" / f).exists():
            bad.append(f"scripts/{f}")
    if bad:
        c.add(FAIL, "S06", f"SKILL.md 点名但文件不存在：{bad}。"
                            "模型照着加载表去找，找不到就自由发挥")
    elif refs_named or scripts_named:
        c.add(OK, "S06", f"点名的 {len(refs_named)} 份 reference、{len(scripts_named)} 个脚本全部存在")

    refs_dir = c.root / "references"
    have = sorted(p.name for p in refs_dir.glob("[0-9][0-9]-*.md")) if refs_dir.exists() else []
    nums = [int(n[:2]) for n in have]
    gaps = [n for n in range(max(nums) + 1) if n not in nums] if nums else []
    if gaps:
        c.add(FAIL, "S07", f"references 编号断号：缺 {gaps}（现有 {nums}）")
    elif nums:
        c.add(OK, "S07", f"references 编号连续（00–{max(nums):02d}）")
    else:
        c.add(WARN, "S07", "没有 numbered references")

    if have:
        orphans = [f for f in have if f not in refs_named]
        if orphans:
            c.add(WARN, "S08", f"孤儿文件（存在但加载表没提）：{orphans}")
        else:
            c.add(OK, "S08", "无孤儿参考文件")

    if assets_named:
        missing = [a for a in sorted(assets_named) if not (c.root / "assets" / a).exists()]
        if missing:
            c.add(FAIL, "S09", f"assets 点名但不存在：{missing}")
        else:
            c.add(OK, "S09", "assets 引用完整")
    else:
        c.add(OK, "S09", "未引用 assets，无需检查")


def check_version(c: Ctx, text, meta):
    if not meta:
        return
    v = meta.get("version", "")
    m = re.search(r"当前\s*([0-9]+\.[0-9]+\.[0-9]+)", text)
    body_v = m.group(1) if m else None
    cl = c.read(c.root / "CHANGELOG.md")
    mc = re.search(r"^##\s*([0-9]+\.[0-9]+\.[0-9]+)", cl, re.M)
    cl_v = mc.group(1) if mc else None

    bad = []
    if body_v != v:
        bad.append(f"正文写「当前 {body_v}」，frontmatter 写 {v}")
    if cl_v != v:
        bad.append(f"CHANGELOG 首条是 {cl_v}，frontmatter 是 {v}")
    if bad:
        c.add(FAIL, "S10", "；".join(bad))
    else:
        c.add(OK, "S10", f"版本三处一致（{v}）")


def check_changelog(c: Ctx):
    cl = c.read(c.root / "CHANGELOG.md")
    if not cl:
        c.add(FAIL, "S11", "CHANGELOG.md 不存在或为空")
        return
    heads = re.findall(r"^##\s*([0-9]+\.[0-9]+\.[0-9]+)(.*)$", cl, re.M)
    if not heads:
        c.add(FAIL, "S11", "CHANGELOG 里没有任何版本条目")
        return
    nodate = [h[0] for h in heads if not re.search(r"\d{4}-\d{2}-\d{2}", h[1])]
    nums = [tuple(int(x) for x in h[0].split(".")) for h in heads]
    ordered = nums == sorted(nums, reverse=True)
    if nodate:
        c.add(WARN, "S11", f"这些版本条目没有日期：{nodate}")
    if not ordered:
        c.add(WARN, "S11", "CHANGELOG 版本顺序不是从新到旧")
    if not nodate and ordered:
        c.add(OK, "S11", f"CHANGELOG {len(heads)} 条，顺序正确、均有日期")


def check_placeholders(c: Ctx):
    """残留的 TODO / 待补 / 占位，是「做了一半」最硬的证据。"""
    pat = re.compile(r"TODO|FIXME|XXX|待补|待写|尚未建成|占位符")
    hits = []
    for p in sorted(c.root.rglob("*.md")):
        if p.name in ("CHANGELOG.md", "TESTS.md"):
            continue  # 变更史和测试记录里出现这些词是史实
        for i, line in enumerate(c.read(p).split("\n"), 1):
            if pat.search(line):
                hits.append(f"{p.relative_to(c.root)}:{i}")
    if hits:
        c.add(FAIL, "S12", f"发现 {len(hits)} 处占位/未完成标记：{hits[:6]}")
    else:
        c.add(OK, "S12", "无占位标记")


def check_hygiene(c: Ctx):
    dirty = [d for d in FORBIDDEN_DIRS if (c.root / d).exists()]
    if dirty:
        c.add(WARN, "S13", f"包内存放了不该有的目录：{dirty}（运行时数据应放使用者工作区）")
    else:
        c.add(OK, "S13", "包内无运行时数据")

    min_lines = int(c.cfg.get("min_lines", DEFAULT_MIN_LINES))
    refs_dir = c.root / "references"
    pool = list(refs_dir.glob("*.md")) if refs_dir.exists() else []
    pool += list(c.root.glob("*.md"))
    thin = []
    for p in sorted(pool):
        n = len(c.read(p).split("\n"))
        if n < min_lines:
            thin.append(f"{p.name}({n} 行)")
    if thin:
        c.add(WARN, "S14", f"内容过薄，疑似占位：{thin}")
    else:
        c.add(OK, "S14", f"无过薄文件（阈值 {min_lines} 行）")


def check_message_script(c: Ctx):
    cm = c.root / "scripts" / "check_message.py"
    if not cm.exists():
        c.add(FAIL, "S15", "scripts/check_message.py 不存在，消息层没有任何机器检查")
        return
    try:
        r = subprocess.run([sys.executable, str(cm), "--selftest"],
                           capture_output=True, text=True, timeout=90)
        out = (r.stdout or "").strip()
        tail = out.split("\n")[-1] if out else ""
        if r.returncode != 0 or "失败" in tail:
            c.add(FAIL, "S15", f"check_message.py 自测未通过：{tail[:80]}")
        else:
            c.add(OK, "S15", f"check_message.py 自测通过（{tail[:50]}）")
    except Exception as e:
        c.add(FAIL, "S15", f"自测跑不起来：{e}")


def check_dead_phrases(c: Ctx):
    """被推翻过的口径。references 里再出现（除否定语境），就是条款改了、执行文件没改。"""
    dead = c.cfg.get("dead_phrases") or []
    if not dead:
        c.add(OK, "S16", "未配置旧口径清单，跳过（.clone2.json 的 dead_phrases）")
        return
    exempt = ["不许", "不要", "禁止", "反例", "错在", "写成", "已废除",
              "废掉", "长什么样", "违反", "曾经", "原来写", "旧口径"]
    hits = []
    refs_dir = c.root / "references"
    for p in sorted(refs_dir.glob("*.md")) if refs_dir.exists() else []:
        for i, line in enumerate(c.read(p).split("\n"), 1):
            for d in dead:
                if d and d in line and not any(k in line for k in exempt):
                    hits.append(f"{p.name}:{i}「{d}」")
    if hits:
        c.add(FAIL, "S16", f"references 里残留已废除的旧口径 {len(hits)} 处：{hits[:5]}。"
                            "条款改了执行文件没改，输出就会退回去")
    else:
        c.add(OK, "S16", f"references 无已废除的旧口径（清单 {len(dead)} 条）")


def find_demo(c: Ctx):
    refs_dir = c.root / "references"
    named = c.cfg.get("demo_file")
    if named and (c.root / named).exists():
        return c.root / named
    if not refs_dir.exists():
        return None
    cands = sorted(refs_dir.glob("*demo*.md")) + sorted(refs_dir.glob("*样本*.md"))
    return cands[0] if cands else None


def check_demo_sync(c: Ctx):
    """样本里的每条消息，必须过得了 check_message.py。

    这是条款和示例的机器绑定：条款改了、示例没改，这里就会红。
    """
    demo = find_demo(c)
    cm = c.root / "scripts" / "check_message.py"
    if demo is None:
        c.add(WARN, "S17", "找不到样本文件（references 下名字含 demo 或 样本），无法绑定条款与示例")
        return
    if not cm.exists():
        c.add(WARN, "S17", "缺 check_message.py，无法校验样本")
        return

    blocks, cur = [], []
    for line in c.read(demo).split("\n"):
        if line.startswith(">"):
            cur.append(line[1:].lstrip())
        else:
            if cur:
                blocks.append("\n".join(cur))
                cur = []
    if cur:
        blocks.append("\n".join(cur))

    blocks = [b for b in blocks if len(b.strip()) >= 10]
    bad = []
    for i, b in enumerate(blocks, 1):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        Path(path).write_text(b, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(cm), path],
                               capture_output=True, text=True, timeout=60)
            out = (r.stdout or "") + (r.stderr or "")
            if "FAIL" in out:
                first = [l.strip() for l in out.split("\n") if "FAIL" in l]
                bad.append(f"第{i}条：{first[0][7:47] if first else '不合格'}")
        finally:
            os.unlink(path)

    if bad:
        c.add(FAIL, "S17", f"样本有 {len(bad)} 条消息过不了 check_message：{bad[:3]}。"
                            "示例比条款更容易被模仿，示例错了等于规则没改")
    else:
        c.add(OK, "S17", f"样本 {len(blocks)} 条消息全部通过 check_message")


def check_skill_body(c: Ctx, text):
    if not text:
        return
    if re.search(r"加载策略|按需加载|什么时候读", text):
        c.add(OK, "S18", "有加载策略")
    else:
        c.add(WARN, "S18", "SKILL.md 没有加载策略。细节该按需读，不该全塞进常驻上下文")

    if re.search(r"第\s*[一二三四五1-5]\s*步|流程|流水线", text):
        c.add(OK, "S19", "有明确流程")
    else:
        c.add(WARN, "S19", "SKILL.md 看不出流程。模型不知道先做什么后做什么")

    if re.search(r"做不到|诚实边界|边界|失效条件", text):
        c.add(OK, "S20", "有诚实边界")
    else:
        c.add(WARN, "S20", "SKILL.md 没写做不到什么。包说得太满，用户第一次失败就不信了")


# ── 入口 ─────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", default=None, help="技能目录，默认脚本上一级")
    ap.add_argument("--strict", action="store_true", help="WARN 也当失败")
    ap.add_argument("--list", action="store_true", help="只列规则")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if args.list:
        for code, desc in RULES:
            print(f"{code}  {desc}")
        return 0

    root = Path(args.target) if args.target else Path(__file__).resolve().parent.parent
    if not root.exists():
        print(f"目录不存在：{root}")
        return 1

    c = Ctx(root)
    if not args.json:
        print(f"校验对象：{c.root}\n")

    text, meta = check_structure(c)
    check_license(c, meta)
    if text:
        check_references(c, text)
        check_version(c, text, meta)
        check_skill_body(c, text)
    check_changelog(c)
    check_placeholders(c)
    check_hygiene(c)
    check_message_script(c)
    check_dead_phrases(c)
    check_demo_sync(c)

    cnt = c.counts()

    if args.json:
        print(json.dumps({
            "root": str(c.root),
            "ok": cnt[OK], "warn": cnt[WARN], "fail": cnt[FAIL],
            "results": [{"level": l, "code": k, "msg": m} for l, k, m in c.results],
        }, ensure_ascii=False, indent=2))
        return 1 if cnt[FAIL] else 0

    mark = {FAIL: "✗", WARN: "!", OK: "✓"}
    for level in (FAIL, WARN, OK):
        for lv, code, msg in c.results:
            if lv == level:
                print(f"  {mark[lv]} {code}  {msg}")

    print(f"\n{len(RULES)} 条规则：{cnt[OK]} 过 / {cnt[WARN]} 警 / {cnt[FAIL]} 败")

    if cnt[FAIL] or (args.strict and cnt[WARN]):
        print("结论：不合格，先修完再谈交付。")
        return 1
    if cnt[WARN]:
        print("结论：可用，但有隐患。")
        return 0
    print("结论：全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单条消息的结构自检。16 条规则，R1–R16。

用法：
    python3 check_message.py 消息文件.txt
    echo "消息内容" | python3 check_message.py
    python3 check_message.py --selftest      # 自测，13 个样本
    python3 check_message.py --list          # 只列规则
    python3 check_message.py --config a.json 消息.txt

配置查找顺序：--config → 当前目录 .clone2.json → 脚本上级目录 .clone2.json
没有配置就用内置默认值。

只管形状，不管内容对不对。内容靠协议，形状靠这个脚本。

四套排版全部走纯文字符号，不依赖 Markdown 渲染：
    A 描述   裸段落
    B 提问   · 中点开头
    C 方法论 ▍ 开头 + 小标题
    D 动作   中文数字 + 【】 括住

退出码：0 全部通过或有 WARN；1 有 FAIL。
"""

import json
import re
import sys
from pathlib import Path

# ── 默认值（可被 .clone2.json 覆盖）─────────────────────────────

DEFAULT_BANNED = [
    "坚持", "自律", "加油", "战胜自己", "毅力不够",
    "每天打卡", "提升意志力", "相信你可以",
]

DEFAULT_TERMS = [
    "意愿", "动机", "能力", "动作单元", "动作层", "锚点", "保底版",
    "习惯回路", "复利", "自我损耗", "执行意图", "承诺一致", "承诺与一致性",
    "启动成本", "反馈回路", "剂量", "情境线索", "替代行为", "损失厌恶",
    "行为阈值", "正反馈", "内驱力",
]

DEFAULT_PHASE = ["第一段", "第二段", "第三段", "第四段", "第五段"]

# ── 正则 ─────────────────────────────────────────────────────

METHOD_HEAD = re.compile(r"^\s*▍")
CN_NUM_HEAD = re.compile(r"^\s*[一二三四五六七八九十]、")
DOT_HEAD = re.compile(r"^\s*[·・]\s*")
BRACKET_ACTION = re.compile(r"【[^】]+】")
QUESTION = re.compile(r"[？?]\s*$")
PHASE_RE = re.compile(r"现在是第[一二三四五六七八九十](?:阶)?段")

# 动作被写成「先……再……」的串联，会变成流程表，用户一条都不办
SPLIT_ACTION = re.compile(r"先[^，。]{0,12}[，,]\s*(?:再|然后|之后)|先[^，。]{0,12}然后")

# 动作里埋条件，这条动作就不存在了
COND_WORDS = ["有空", "如果", "尽量", "方便的话", "抽空", "要是有时间", "顺便的话"]

# 方法论里会用到、但必须先给定义的抽象名词。裸着出现就是术语裸奔
# 定义标记：出现任何一种，算这个词被交代过
DEF_MARKER = re.compile(r"(说白了|意思是|指的是|所谓|叫做|叫|即|[，,]\s*是|就是|：)")

# 「方法 → 他自己的事」那一段允许第二人称，之前的部分不许
MAPPING_MARK = re.compile(r"(对照本例|放到你这件事上|对应到你|在你的情况|搁在你身上|落到本例)")

# Markdown 符号泄漏。手机端不渲染，这些会原样露出来
LEAK_PATTERNS = [
    (re.compile(r"\*\*"), "** 加粗"),
    (re.compile(r"^\s*>\s", re.M), "> 引用块"),
    (re.compile(r"^\s*---\s*$", re.M), "--- 分隔线"),
    (re.compile(r"^\s*[-*]\s+", re.M), "- 或 * 列表"),
    (re.compile(r"^\s*#{1,6}\s", re.M), "# 标题"),
    (re.compile(r"`{3}"), "``` 代码块"),
]

RULES = [
    ("R1", "长度 ≤400 字（建议 ≤250）"),
    ("R2", "提问不许用中文数字开头"),
    ("R3", "提问 ≤4 条"),
    ("R4", "动作里不许埋条件"),
    ("R5", "方法论块必须有书名或方法名小标题"),
    ("R6", "黑名单词（意志力叙事等）"),
    ("R7", "一条消息只准一个方法论块"),
    ("R8", "动作 ≤3 条"),
    ("R9", "阶段开场四段齐（报阶段／概括句／方法论／提问或动作）"),
    ("R10", "动作里不许有问号"),
    ("R11", "无 Markdown 符号泄漏"),
    ("R12", "方法论前半段不许第二人称"),
    ("R13", "术语不许裸奔"),
    ("R14", "动作不许串成「先……再……」"),
    ("R15", "方法论块必须在动作块之前"),
    ("R16", "结尾必须有提问或动作"),
]


# ── 配置 ─────────────────────────────────────────────────────

def load_config(explicit=None):
    cands = []
    if explicit:
        cands.append(Path(explicit))
    cands.append(Path.cwd() / ".clone2.json")
    cands.append(Path(__file__).resolve().parent.parent / ".clone2.json")
    for p in cands:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")), p
            except Exception:
                continue
    return {}, None


def cfg_list(cfg, key, default):
    v = cfg.get(key)
    return list(v) if isinstance(v, list) and v else list(default)


# ── 工具 ─────────────────────────────────────────────────────

def visible_len(text):
    """中文字符 + 英文单词，粗算用户要读多少。"""
    cn = len(re.findall(r"[\u4e00-\u9fff]", text))
    en = len(re.findall(r"[A-Za-z]+", text))
    return cn + en


def method_blocks(lines):
    """把每个 ▍ 块连到下一个空行为止，整块取出来。"""
    blocks, i = [], 0
    while i < len(lines):
        if METHOD_HEAD.match(lines[i]):
            j = i + 1
            while j < len(lines) and lines[j].strip():
                j += 1
            blocks.append("\n".join(lines[i:j]))
            i = j
        else:
            i += 1
    return blocks


def last_meaningful(lines, k=6):
    return [l for l in lines if l.strip()][-k:]


# ── 主检查 ───────────────────────────────────────────────────

def check(text, cfg=None):
    cfg = cfg or {}
    banned = cfg_list(cfg, "banned_words", DEFAULT_BANNED)
    terms_pool = cfg_list(cfg, "terms", DEFAULT_TERMS)
    phase_words = cfg_list(cfg, "phase_words", DEFAULT_PHASE)

    fails, warns, oks = [], [], []
    lines = text.split("\n")

    # R1 长度（上限可配置：八步清单型消息天然超 400 字，见 .clone2.json 的 max_len）
    max_len = int(cfg.get("max_len", 400) or 400)
    n = visible_len(text)
    if n > max_len:
        fails.append(f"R1 长度超标：约 {n} 字，硬上限 {max_len}。超了用户不看")
    elif n > int(max_len * 0.625):
        warns.append(f"R1 长度偏长：约 {n} 字，建议压到 {int(max_len * 0.625)} 以内")
    else:
        oks.append(f"R1 长度 {n} 字，合格")

    # R11 Markdown 泄漏（最先看，它最毁观感）
    # allow_bold：渲染环境用加粗卡头做架构层指纹时放行，见 .clone2.json
    allow_bold = bool(cfg.get("allow_bold", False))
    patterns = [p for p in LEAK_PATTERNS if not (allow_bold and p[1].startswith("**"))]
    leaks = [name for pat, name in patterns if pat.search(text)]
    if leaks:
        fails.append(f"R11 有 Markdown 符号漏在外面：{leaks}。手机端不渲染，会显示成符号垃圾")
    else:
        oks.append("R11 没有 Markdown 符号泄漏")

    # R2 提问混形：中文数字开头 + 问号结尾
    bad_q = [i + 1 for i, l in enumerate(lines)
             if CN_NUM_HEAD.match(l) and QUESTION.search(l)]
    if bad_q:
        fails.append(f"R2 提问用了中文数字（第 {bad_q} 行）。提问一律中点「·」，"
                     "中文数字是动作的写法，用了就撞形")
    else:
        oks.append("R2 提问没有和动作撞形")

    # R3 提问条数
    dots = [l for l in lines if DOT_HEAD.match(l)]
    if len(dots) > 4:
        warns.append(f"R3 提问 {len(dots)} 条，上限 4 条，超了他会挑着答")
    elif dots:
        oks.append(f"R3 提问 {len(dots)} 条，合格")

    # R8 动作条数
    actions = BRACKET_ACTION.findall(text)
    if len(actions) > 3:
        fails.append(f"R8 动作 {len(actions)} 条，上限 3 条。第四条开始他不做")
    elif actions:
        oks.append(f"R8 动作 {len(actions)} 条，合格")

    # R4 方括号里埋条件
    cond = [a for a in actions if any(w in a for w in COND_WORDS)]
    if cond:
        fails.append(f"R4 动作里埋了条件：{cond[0][:30]}。「有空的话」「如果方便」"
                     "这几个字一加，这条动作就不存在了")

    # R10 方括号里有问号（问了就不是动作）
    asking = [a for a in actions if re.search(r"[？?]", a)]
    if asking:
        fails.append(f"R10 动作里出现问号：{asking[0][:30]}。要问的走提问块，"
                     "别混进动作里，他会以为在征求意见然后不动")

    # R14 动作串成两步
    split = [a for a in actions if SPLIT_ACTION.search(a)]
    if split:
        fails.append(f"R14 动作被拆成两步串联：{split[0][:30]}。写成「先跟他说，再转钱」，"
                     "他会当成流程表，办第一条就散。改法：拆成两条独立动作，一次发完")
    elif actions:
        oks.append("R14 动作没有串成流程")

    # R5 / R7 方法论块
    method_lines = [l for l in lines if METHOD_HEAD.match(l)]
    unnamed = [l for l in method_lines if "《" not in l and "为什么" not in l]
    if unnamed:
        warns.append(f"R5 有 {len(unnamed)} 个 ▍ 后面既没有书名《》，也没有「为什么……」小标题")
    elif method_lines:
        oks.append("R5 方法论块报了出处")

    if len(method_lines) > 1:
        warns.append(f"R7 出现 {len(method_lines)} 个方法论块，一条消息只准一个。"
                     "两个说明你在这条里讲了两件事，拆成两条")
    elif method_lines:
        oks.append("R7 只有一个方法论块")

    # R15 方法论在动作之前
    blocks = method_blocks(lines)
    if actions and method_lines:
        first_m = min(i for i, l in enumerate(lines) if METHOD_HEAD.match(l))
        first_a = min(i for i, l in enumerate(lines) if "【" in l and "】" in l)
        if first_m > first_a:
            fails.append("R15 方法论块在动作块后面。顺序反了他会照做，"
                         "但心里那句「为什么」一直没被消掉，第三天就停")
        else:
            oks.append("R15 方法论在动作之前")

    # R12 / R13 方法论内部
    if blocks:
        personal = []
        for b in blocks:
            pre = MAPPING_MARK.split(b)[0]
            if re.search(r"[你您]", pre):
                personal.append(pre)
        if personal:
            head = personal[0].split("\n")[0][:20]
            fails.append(f"R12 方法论前半段出现了第二人称（{head}…）。「对照本例」"
                         "那一段才允许写「你」，在它之前只准讲通性。出现在前半段，"
                         "说明讲的是这件事的操作细节，不是方法本身")
        else:
            oks.append("R12 方法论讲的是通性，没有落到具体这个人身上")

        naked = []
        for b in blocks:
            hit = [t for t in terms_pool if t in b]
            if hit and not DEF_MARKER.search(b):
                naked.append(hit)
        if naked:
            fails.append(f"R13 方法论里用了没交代过的概念：{naked[0]}。"
                         "这些词对用户是生词，突然拿来当论据等于没说。"
                         "改法：块内第一句先给定义，用「X，指的是……」的句式")
        elif blocks:
            oks.append("R13 方法论里的概念都当场交代过")

    # R6 黑名单
    hits = [w for w in banned if w in text]
    if hits:
        fails.append(f"R6 出现黑名单词：{hits}")
    else:
        oks.append("R6 没有黑名单词")

    # R9 阶段开场四段
    triggered = PHASE_RE.search(text) or any(w in text for w in phase_words)
    if triggered:
        if "只做一件事" not in text:
            fails.append("R9 报了阶段，但没有「这一段只做一件事：……」的概括句")
        elif not re.search(r"只做一件事[：:][^。]{4,}", text):
            warns.append("R9 概括句像是在写机制名。它必须落在他能看见的动作上")
        else:
            oks.append("R9 阶段开场有概括句")
        if not method_lines:
            warns.append("R9 阶段开场缺方法论块（▍）")
        if not dots and not actions:
            warns.append("R9 阶段开场既没有提问也没有动作，他读完不知道下一步干什么")

    # R16 整条消息要有 B 或 D，否则他读完不知道干什么
    has_tail = bool(dots) or bool(actions)
    if not has_tail:
        fails.append("R16 通篇既没有提问也没有动作。他读完只会以为你在讲道理，"
                     "这次对话到此为止。至少补一句「· 你看对不对」，或一条【动作】")
    else:
        oks.append("R16 有事可做")

    return fails, warns, oks


# ── 输出 ─────────────────────────────────────────────────────

def report(text, cfg=None, quiet=False):
    fails, warns, oks = check(text, cfg)
    if not quiet:
        for x in oks:
            print(f"  PASS  {x}")
        for x in warns:
            print(f"  WARN  {x}")
        for x in fails:
            print(f"  FAIL  {x}")
        if not fails and not warns:
            print("\n可以发。")
        elif not fails:
            print("\n能发，但有几处可以收一收。")
        else:
            print("\n别发。先把 FAIL 改掉。")
    return 1 if fails else 0


# ── 自测 ─────────────────────────────────────────────────────

GOOD = """现在是第一段。这一段只做一件事：把第一句话换成一个他能答的问题。

▍《SPIN 销售法》中的背景问题
该方法认为，一次有效的推进始于信息不对称的消除。第一步是背景问题，指的是围绕客户现状提出的、对方不用思考就能回答的事实型问题。
对照本例：名单已有，背景信息几乎空白；第一句直接自我介绍，跳过了这一步。

因此本次只替换第一句话，风格不动。

今晚挑三个人试：

一、【从名单里挑三个同行业的人，各写一条只问事实的消息】

二、【三条发出去，把发出时间记下来】

· 明天几点提醒你合适，九点还是两点？"""

SELFTEST = {
    "合格样本": GOOD,
    "Markdown 符号泄漏": """现在是第一段。这一段只做一件事：改摆法。

> **为什么这么设计**
> 记录会改变行为。

- 九点
- 两点
""",
    "提问用了中文数字": """先问两件：

一、你想找谁？

二、照片哪天发？
""",
    "动作四条": """今晚做四件事：

一、【把甲挪到乙】

二、【把丙挪到丁】

三、【把戊拿出来】

四、【拍张照】
""",
    "动作串成两步": """行，就这么办。

现在去：

一、【先跟对方说清楚，再签字】

二、【签完拍照给我】
""",
    "动作埋条件": """今晚一件事：

一、【有空的话把垫子铺开】
""",
    "动作里带问号": """先确认一下：

一、【问问他周三还是周四方便？】

二、【把结果发我】
""",
    "方法论写成这件事的说明书": """现在是第一段。这一段只做一件事：改门口。

▍为什么是三件小事
动机高的时候才推得动。车在楼下没挪，你下楼就会先往地铁口走。

今晚一件事：

一、【把车挪到你出楼门看见的地方】
""",
    "方法论里术语裸奔": """现在是第一段，只做一件事：改摆法。

▍为什么先降难度
意愿会飘，难度能改，所以先动难度。

今晚一件事：

一、【把车挪出来】
""",
    "方法论后置": """现在是第一段。这一段只做一件事：改摆法。

一、【把车挪出来】

▍《福格行为模型》中的行为发生条件
该模型提出，行为的成立需要动机、能力、提示同时具备。
对照本例：缺口在提示。

因此本次只动提示。
""",
    "报阶段无概括句": """现在是第二阶段。上一步摆好了。

▍为什么要有外人
该原则指的是，人对自己的判断没有裁判权。

· 你想找谁？
""",
    "黑名单": "你要坚持下去，靠自律，加油。",
    "通篇没有动作和提问": """现在是第一段。这一段只做一件事：改摆法。

▍《福格行为模型》中的提示
提示，指的是触发行为的外部线索。
对照本例：缺口在提示。

因此本次只动提示。

弄完了跟我说一声就好，剩下的下次再说。""",
}


def selftest():
    bad = 0
    total = len(SELFTEST)
    for name, text in SELFTEST.items():
        code = report(text, quiet=True)
        expect_fail = name != "合格样本"
        if bool(code) != expect_fail:
            print(f"  !! {name}：期望 {'有 FAIL' if expect_fail else '无 FAIL'}")
            report(text)
            bad += 1
    print(f"自测 {total} 项：{'通过' if bad == 0 else f'失败 {bad} 项'}")
    return 1 if bad else 0


# ── 入口 ─────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    explicit_cfg = None
    if "--config" in args:
        i = args.index("--config")
        explicit_cfg = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]

    if args and args[0] == "--list":
        for code, desc in RULES:
            print(f"{code}  {desc}")
        return 0

    cfg, path = load_config(explicit_cfg)

    if args and args[0] == "--selftest":
        return selftest()

    if args:
        text = Path(args[0]).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    if path and "--quiet-config" not in args:
        print(f"配置：{path}\n")
    return report(text, cfg)


if __name__ == "__main__":
    sys.exit(main())

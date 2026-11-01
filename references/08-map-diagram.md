# 08 · 出图模板（第 1 步必须渲染）

第 1 步「出图」要给用户一张能一眼扫完的图，不是把四层铺成文字墙。做法：读这个文件，把下面这段 SVG 原样传给可视化工具（show_widget，render_mode=svg）渲染出来。

这张图是固定的框架模板——四层沟通地图（局面／目标／结构／话术）＋八步流程（标出用户在哪几步拍板）。它不填用户的具体数据，用户情况在第 2、3 步才进场。文字只在图前后各留一两句引导，绝不再把四层逐条重写。

合规要点（可视化工具规范）：viewBox 固定 `0 0 680 H`；外框透明（主机提供背景）；字号不小于 11px；只用 400／500 两种字重；扁平、浅底深字、无渐变无阴影。

```svg
<svg viewBox="0 0 680 540" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system, 'Segoe UI', 'Microsoft YaHei', sans-serif" role="img">
  <title>沟通地图：四层 + 八步流程</title>
  <desc>四层沟通地图（局面、目标、结构、话术）从上往下垒，下方是八步流程并标出用户在补缺口、判断目标、框架、材料、应对、红线、定时这几步拍板。</desc>

  <text x="40" y="30" font-size="15" font-weight="500" fill="#1f2328">沟通地图 · 四层 + 八步流程</text>
  <text x="40" y="48" font-size="12" font-weight="400" fill="#57606a">设计从图纸开始，不从话术开始；下一层不成立，就不往上走。</text>

  <rect x="40" y="60" width="600" height="72" rx="8" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <path d="M40 68 a8 8 0 0 1 8 -8 h134 a8 8 0 0 1 8 8 v56 a8 8 0 0 1 -8 8 h-134 a8 8 0 0 1 -8 -8 z" fill="#185FA5"/>
  <text x="54" y="90" font-size="13" font-weight="500" fill="#ffffff">第一层 局面</text>
  <text x="54" y="110" font-size="12" font-weight="400" fill="#ffffff">能不能谈</text>
  <text x="204" y="88" font-size="13" font-weight="500" fill="#1f2328">关系存量 · 权力差 · 他的约束 · 你的筹码</text>
  <text x="204" y="110" font-size="12" font-weight="400" fill="#57606a">判错局面，话术越好死得越快</text>

  <path d="M322 133 l16 0 l-8 10 z" fill="#8b949e"/>

  <rect x="40" y="144" width="600" height="72" rx="8" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <path d="M40 152 a8 8 0 0 1 8 -8 h134 a8 8 0 0 1 8 8 v56 a8 8 0 0 1 -8 8 h-134 a8 8 0 0 1 -8 -8 z" fill="#0F6E56"/>
  <text x="54" y="174" font-size="13" font-weight="500" fill="#ffffff">第二层 目标</text>
  <text x="54" y="194" font-size="12" font-weight="400" fill="#ffffff">谈到哪</text>
  <text x="204" y="172" font-size="13" font-weight="500" fill="#1f2328">要什么 · 可让区间 · 底线 · BATNA（退路）</text>
  <text x="204" y="194" font-size="12" font-weight="400" fill="#57606a">说不出底线，一压就让</text>

  <path d="M322 217 l16 0 l-8 10 z" fill="#8b949e"/>

  <rect x="40" y="228" width="600" height="72" rx="8" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <path d="M40 236 a8 8 0 0 1 8 -8 h134 a8 8 0 0 1 8 8 v56 a8 8 0 0 1 -8 8 h-134 a8 8 0 0 1 -8 -8 z" fill="#BA7517"/>
  <text x="54" y="258" font-size="13" font-weight="500" fill="#ffffff">第三层 结构</text>
  <text x="54" y="278" font-size="12" font-weight="400" fill="#ffffff">怎么走</text>
  <text x="204" y="256" font-size="13" font-weight="500" fill="#1f2328">六段：开场 · 事实 · 请求 · 反应 · 异议 · 收口</text>
  <text x="204" y="278" font-size="12" font-weight="400" fill="#57606a">总时长 ≤ 8 分钟；没结构就变聊天</text>

  <path d="M322 301 l16 0 l-8 10 z" fill="#8b949e"/>

  <rect x="40" y="312" width="600" height="72" rx="8" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <path d="M40 320 a8 8 0 0 1 8 -8 h134 a8 8 0 0 1 8 8 v56 a8 8 0 0 1 -8 8 h-134 a8 8 0 0 1 -8 -8 z" fill="#534AB7"/>
  <text x="54" y="342" font-size="13" font-weight="500" fill="#ffffff">第四层 话术</text>
  <text x="54" y="362" font-size="12" font-weight="400" fill="#ffffff">说什么</text>
  <text x="204" y="340" font-size="13" font-weight="500" fill="#1f2328">每段一句核心诉求 + 应对卡（第 6 步）</text>
  <text x="204" y="362" font-size="12" font-weight="400" fill="#57606a">只有这一层，等于给人没装子弹的枪</text>

  <text x="40" y="412" font-size="13" font-weight="500" fill="#1f2328">本次八步流程（你在哪拍板）</text>

  <rect x="42" y="426" width="68" height="38" rx="6" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <text x="76" y="445" font-size="12" font-weight="400" fill="#1f2328" text-anchor="middle" dominant-baseline="central">出图</text>
  <text x="114" y="445" font-size="14" font-weight="400" fill="#8b949e" text-anchor="middle" dominant-baseline="central">›</text>

  <rect x="118" y="426" width="68" height="38" rx="6" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <text x="152" y="445" font-size="12" font-weight="400" fill="#1f2328" text-anchor="middle" dominant-baseline="central">补缺口</text>
  <text x="190" y="445" font-size="14" font-weight="400" fill="#8b949e" text-anchor="middle" dominant-baseline="central">›</text>

  <rect x="194" y="426" width="68" height="38" rx="6" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <text x="228" y="445" font-size="12" font-weight="400" fill="#1f2328" text-anchor="middle" dominant-baseline="central">判断目标</text>
  <text x="266" y="445" font-size="14" font-weight="400" fill="#8b949e" text-anchor="middle" dominant-baseline="central">›</text>

  <rect x="270" y="426" width="68" height="38" rx="6" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <text x="304" y="445" font-size="12" font-weight="400" fill="#1f2328" text-anchor="middle" dominant-baseline="central">框架</text>
  <text x="342" y="445" font-size="14" font-weight="400" fill="#8b949e" text-anchor="middle" dominant-baseline="central">›</text>

  <rect x="346" y="426" width="68" height="38" rx="6" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <text x="380" y="445" font-size="12" font-weight="400" fill="#1f2328" text-anchor="middle" dominant-baseline="central">材料</text>
  <text x="418" y="445" font-size="14" font-weight="400" fill="#8b949e" text-anchor="middle" dominant-baseline="central">›</text>

  <rect x="422" y="426" width="68" height="38" rx="6" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <text x="456" y="445" font-size="12" font-weight="400" fill="#1f2328" text-anchor="middle" dominant-baseline="central">应对</text>
  <text x="494" y="445" font-size="14" font-weight="400" fill="#8b949e" text-anchor="middle" dominant-baseline="central">›</text>

  <rect x="498" y="426" width="68" height="38" rx="6" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <text x="532" y="445" font-size="12" font-weight="400" fill="#1f2328" text-anchor="middle" dominant-baseline="central">红线</text>
  <text x="570" y="445" font-size="14" font-weight="400" fill="#8b949e" text-anchor="middle" dominant-baseline="central">›</text>

  <rect x="574" y="426" width="68" height="38" rx="6" fill="#ffffff" stroke="#d0d7de" stroke-width="0.5"/>
  <text x="608" y="445" font-size="12" font-weight="400" fill="#1f2328" text-anchor="middle" dominant-baseline="central">回访</text>

  <text x="42" y="490" font-size="11" font-weight="400" fill="#57606a">你拍板：补缺口 · 判断目标 · 框架 · 材料 · 应对 · 红线 · 定时（图与流程由我出）</text>
</svg>
```

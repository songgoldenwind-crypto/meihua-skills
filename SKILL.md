---
name: meihua-divination
description: 用于完整梅花易数流程：时间、数字、文字笔画、物数声数、尺寸、人物物象、方位与外应起卦，以及先后天口径、体互用互、卦气旺衰、三要十应、分类占、观物、本互变和应期分析。不用于铜钱六爻装卦、八字或单纯拆字。
---

# 梅花易数

围绕一个明确问题，按“固定起法 → 复核本互变 → 定体用 → 看生克与过程 → 合真实外应 → 收束事项与时间”推断。术数判断只表达该体系内的象意和趋势，不写成已证实的现实事实。

本 Skill 只公开可执行的方法、输入条件和判断边界，不列书名、作者、版本、页码或资料路径。默认起卦、体用、分类占、三要十应和观物的范围见 [方法覆盖表](references/14-method-coverage.md)。可选方法须明确指定并按 [方法分流](references/15-method-routing.md) 独立使用；不能把策轨、卦组、六亲或日月标签混进一张默认盘。测字和六爻是可选的其他 Skill。

## 任务路由

先按用户真正要做的事选入口，再读对应参考文件；不要默认加载全部资料。

| 用户输入或任务 | 主入口 | 必读参考 |
| --- | --- | --- |
| 公历/农历时间、两个或三个数字、物数、声数、丈尺、尺寸、字数或确认笔画起卦 | 纯梅花起卦 | [01-casting-methods.md](references/01-casting-methods.md)、[02-body-use.md](references/02-body-use.md) |
| 明确要求按抓米两次数法起卦，且有两次计数与时支 | 现代抓米法 | [01-casting-methods.md](references/01-casting-methods.md) 的专节；标签与默认两数法分开 |
| 人物身份、动作、所持物、服色、动物、静物异常或方位直接起卦 | 后天端法 | [01-casting-methods.md](references/01-casting-methods.md)、[03-external-omens.md](references/03-external-omens.md)、[10-three-essentials.md](references/10-three-essentials.md) |
| 已有一卦，要求完整体用、生克、旺衰、本互变或冲突裁决 | 体用主链 | [02-body-use.md](references/02-body-use.md)、[06-advanced-interpretation.md](references/06-advanced-interpretation.md)、[09-interpretive-principles.md](references/09-interpretive-principles.md) |
| 工作、考试、求财、交易、婚恋、出行、行人、失物、住居、天气等具体事项 | 分类占 | [05-topic-reading.md](references/05-topic-reading.md)，再按需读 [04-timing.md](references/04-timing.md) |
| 现场所见所闻、三要、十应、真假外应、来去向背 | 外应与克应 | [03-external-omens.md](references/03-external-omens.md)、[10-three-essentials.md](references/10-three-essentials.md)、[06-advanced-interpretation.md](references/06-advanced-interpretation.md) |
| 猜物、辨形、辨色、材质、数量、饮食或器物成败 | 观物 | [11-object-reading.md](references/11-object-reading.md)、[07-trigram-images.md](references/07-trigram-images.md) |
| 需要重卦名义、相反相成、动止聚散等限制语 | 重卦语义 | [12-hexagram-natures.md](references/12-hexagram-natures.md)；只作主链限制，不凭卦名单断 |
| 屋宅、店铺、环境观察或传统宅象 | 环境占 | [13-house-environment.md](references/13-house-environment.md)、[05-topic-reading.md](references/05-topic-reading.md) |
| 需要卦辞、爻辞辅助，或区分先天数卦与后天端法 | 易辞与理数 | [09-interpretive-principles.md](references/09-interpretive-principles.md)； exact wording 只用已核实文本 |
| 校验经典案例或复盘旧断 | 方法回测 | [08-classic-cases.md](references/08-classic-cases.md) |
| 明确指定策轨身数、乘加或古音挂一定位 | 策轨与古音独立层 | [18-cegui-phonetic.md](references/18-cegui-phonetic.md)；已核卦爻与已核声/音卦分别走对应辅助器 |
| 明确指定太极点、卦组与月令五态 | 太极点独立层 | [19-taiji-overlay.md](references/19-taiji-overlay.md)；先定太极点及理由，再看卦内关系与条件应期 |
| 明确指定飞宫五行、日月标签 | 飞宫独立层 | [20-flying-overlay.md](references/20-flying-overlay.md)；起数固定后再输出标签 |
| 明确问手机号数位结构 | 数码独立层 | [21-number-profile.md](references/21-number-profile.md)；列候选，不与末四位起卦混用 |
| 比较不同算法的适用范围 | 方法比较 | [15-method-routing.md](references/15-method-routing.md)；只比较输入与输出边界，不拼盘 |
| 单字拆字、添减笔、音义测字 | 可选 `character-divination` | 未安装时说明本 Skill 只能处理已核笔画的梅花字数卦 |
| “梅起爻断”、象数成卦后装纳甲 | 可选 `liuyao-divination` | 未安装时只提供梅花本卦和单动爻，不临时装六爻盘 |
| 铜钱或六次老少阴阳 | 六爻方法 | 本 Skill 不改造成梅花单动爻盘 |

若用户同时提出多个入口，优先遵从其明确指定的方法；未指定时选择与原始输入最直接且可复核的一种。只有用户明确要求比较方法时才分栏执行，不能多起数卦后挑结论。

## 先固定输入

记录占问、对象、期限、实际触发、起卦时间与时区，以及用户选定的起法。用户已经指定起法时不得更换；未指定时只根据已经存在的输入选一种最自然、可复核的方法，不同时起多卦挑结论。

- 只给公历时间并明确要求时间起卦：换算当地农历年月日和时支后起卦。
- 给出数字、物数、声音次数、丈尺或明确上下卦：采用相应数法。
- 因一个当时发生的异常动作、来物、声响或方位而起念：可用后天外应法。
- 只给六次老少阴阳或铜钱结果：如环境中已安装六爻 Skill 则转用；否则说明本 Skill 不处理该起法。
- 只给一个字并要求拆字：如已安装测字 Skill 则转用；否则只有笔画数经独立核实时才能按梅花数卦处理。
- 明确要求“梅起爻断”“梅花起卦后按六爻断”或“象数起卦后装纳甲”：如已安装六爻 Skill 则交给其正式装卦流程。本 Skill 只提供本卦和单动爻，不把体用、互卦当成六爻断据。

各种起法、先后天口径、文字与人物物象公式、余数规则和适用条件见 [01-casting-methods.md](references/01-casting-methods.md)。

## 可执行排盘

以下脚本路径均以本 `SKILL.md` 所在目录为基准；从其他工作目录调用时先定位该目录，不能假定当前目录就是 Skill 所在位置。

需要计算本卦、互卦、变卦和体用时，必须使用 `scripts/meihua-engine/`，不要在回答中临时手算或自行编写排盘逻辑。内置排盘核心和历法库的必要开源许可见 [第三方声明](THIRD_PARTY_NOTICES.md)。本地 `paipan.py` 只做输入校验、调用固定版本函数和 JSON 输出归一化，无需联网安装依赖。

手工指定上下卦和动爻：

```bash
python3 scripts/meihua-engine/paipan.py manual --upper 震 --lower 离 --moving-line 3
```

已知农历年支、月、日、时支：

```bash
python3 scripts/meihua-engine/paipan.py lunar-time --year-branch 午 --month 8 --day 5 --hour-branch 午
```

公历时间起卦使用当地墙钟时间和 IANA 时区：

```bash
python3 scripts/meihua-engine/paipan.py time --datetime 2026-09-15T11:00 --timezone Asia/Shanghai
```

数字、笔画和声数分别使用 `numbers`、`strokes` 和 `sound` 子命令；参数格式见脚本目录的 [README.md](scripts/meihua-engine/README.md)。脚本输出必须保留 `engine`、`calendar_engine`、`method`、原始输入和 `source_trace`，并明确 `body_position`、`use_position`、`body_mutual`、`use_mutual`；提供实际占问时间时还会生成 `seasonal_qi`。数字、笔画、声音、手工卦和外应使用 `--context-datetime` 记录事件时间，该参数只补历法与卦气，不进入原起卦算式。脚本负责确定性排盘，不自动替代取象和判断。公历入口按用户指定的 IANA 时区解释民用时间，分钟不入梅花起卦数；闰月按同名本月数计算。日干支字段采用 23:00 晚子换日并在输出中明示；它只供指定异法取用，不改变默认梅花原卦。若用户指定真太阳时、子正换日或其他口径，应先取得该口径下核实的历法值，不暗改引擎或用不相容的日干支叠加解释。

明确指定独立方法时，按 [辅助器说明](scripts/source-variants/README.md) 调程序。`flying` 输出飞宫五行与日月标签；`taiji` 要求先固定太极点及理由，列卦内关系、月令五态与条件应期；`number` 分析数字位、四格、三合对应和变数表；`cegui` 计算已核卦爻的策轨身数及乘加；`phonetic` 要求先核声卦和音卦，再复算横合及挂一图位。除 `number`、`phonetic` 外先保存上述排盘 JSON。它们均不改动已排的本互变；缺少完整判据的步骤不由程序自动补全。

## 外应起卦的强制顺序

先把外应固定为一种身份，不可在同一回答中既称它为旁证又称它为独立卦：

- **原场景旁证：** 时间、数字或其他方法已经成卦，异常现象与该次起卦发生在同一现场。它只确认、削弱或限定原局，不再起卦。
- **外应直接起卦：** 异常现象就是本次最初的起卦入口。执行“模型取象 → 冻结依据 → 程序排盘 → 模型解读”。
- **新事件复占：** 原卦完成后又真实发生新的突发事件，且用户明确要求用该新事件起卦，可以另成一局。标明这是新触发的复占，先独立解读，再与原卦比较共同信息和冲突；新卦不得覆盖或改写原卦。

记录事件实际发生时间。用户明确表示“刚才、突然、刚刚”且对话没有明显延迟时，可以用系统接收时刻代记，但须标明这是代记时刻；事件并非刚刚发生时必须取得用户提供的发生时间，不以读取系统时间冒充事件时间。

外应本身起卦时按以下顺序执行：

1. 模型先核实它与起念同步、真实发生、相对日常异常并与所问相关。条件不够就停止外应起卦，不从环境中补找符号。
2. 模型只完成取象：选一个主物象，根据当时最突出的真实作用或动作定物象卦；根据实际来方定方位卦；按现场时间确认时支。把“原始现象 → 采用特征 → 对应卦”和方位依据写定后，不得因排盘结果改配。
3. 调用下列接口。模型不得自己取余、翻爻、推互卦、定变卦或定体用：

```bash
python3 scripts/meihua-engine/paipan.py external-omen \
  --object-trigram 震 --object-evidence "车辆突然启动，以动态取震" \
  --direction-trigram 离 --direction-evidence "车辆从正南方来" \
  --hour-branch 申 \
  --context-datetime 2026-09-15T15:00 --timezone Asia/Shanghai
```

4. 以程序返回的 `original`、`moving_line`、`mutual`、`changed` 与 `body_use` 为唯一盘面。程序失败时说明无法完成排盘，不凭记忆补盘。
5. 模型最后结合占问解释体用生克、本互变过程与应期；原始外应可以帮助限定象义，但不能反向修改已经冻结的上下卦。属于新事件复占时，另列与原卦的共同点、冲突和各自支持的现实阶段，不拼接两卦的有利片段。

## 判断顺序

1. **核本互变。** 八卦数为乾一、兑二、离三、震四、巽五、坎六、艮七、坤八；除八余零取坤，除六余零取上爻。互卦以下互取二三四爻、上互取三四五爻。
2. **定体用。** 动爻所在经卦为用，另一经卦为体。体代表所问主体或承受方，用代表所问之事、对方或作用方。详细规则见 [02-body-use.md](references/02-body-use.md)。
3. **定解释口径。** 区分先天数卦与后天端法，决定卦辞、爻辞和现场之理怎样参与；先读 [09-interpretive-principles.md](references/09-interpretive-principles.md)，不得把古例的具体事件复制到新卦。
4. **排过程与强弱。** 本卦看当前直接关系，体互看主体中段、用互看事项中段，变卦看末段；再用月支卦气调整承受力。读取 [06-advanced-interpretation.md](references/06-advanced-interpretation.md)。
5. **合外应。** 已有卦局时，只使用起卦时真实、同步、与问题有明确关系的所见所闻；记录“现象 → 对应卦象 → 真假轻重、向背动静 → 如何改变主判断”，不因旁证重起一卦。若外应本身用于起卦，必须先完成上面的强制顺序。读取 [03-external-omens.md](references/03-external-omens.md)；需要细分耳目心、人物、器物、动植物、言语和声音时再读 [10-three-essentials.md](references/10-three-essentials.md)。
6. **按题细化。** 十八类传统占和现代工作、考试、项目、关系等读取 [05-topic-reading.md](references/05-topic-reading.md)。先拆现实阶段，再判断卦局最远支持到哪一步。
7. **定应期。** 先写清最多支持到“消息、面试、确认、完成”的哪一层；该层没有成立证据就不报其日期。读取 [04-timing.md](references/04-timing.md)。使用太极点法时还须核 [19-taiji-overlay.md](references/19-taiji-overlay.md) 的条件是否已满足；程序给出的纳支候选、单一卦数或季节五行，均不得单独换算为事项完成时间。用户同题反复问卦而没有新事件时，回到原卦与现实进展，不为迎合新结论重起。

需要把卦落实到人物、动作、器物或场所时读取 [07-trigram-images.md](references/07-trigram-images.md)，每个经卦只保留与主链直接相关的一至两个象。观物、饮食和器物成败另读 [11-object-reading.md](references/11-object-reading.md)；重卦名义只在 [12-hexagram-natures.md](references/12-hexagram-natures.md) 的限定范围使用。需要校验推理步骤时读取 [08-classic-cases.md](references/08-classic-cases.md)；古例只验证方法，不复制具体结果。

## 输出

默认按下列顺序收束：

- **判断：** 一至三句直接回答所问，并说明能推进到哪个现实阶段。
- **排盘依据：** 起法、关键算式、本卦、动爻、互卦、变卦及体用。
- **主链：** 体用生克如何从本卦经互卦走到变卦，只保留决定结果的两至四个节点。
- **外应与应期：** 有真实外应才写其加强、减弱或限定作用；只有阶段、尺度和方法前提均成立时才给时间窗，否则说明快慢或触发线索。
- **限制：** 写出最可能改变判断的一项缺失条件或反证。

不要把卦名故事、颜色、动物、声音和方位逐项堆成多条互不约束的解释。卦象不用于医疗诊断、死亡断言、犯罪指认、胎儿性别、他人隐私事实或证券交易保证；现实行动以事实和专业意见为依据。

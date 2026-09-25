# 梅花易数开源排盘适配器

排盘核心与历法转换依赖以固定版本随 Skill 内置，无需联网安装。第三方 MIT 许可证和必要署名见 [第三方声明](THIRD_PARTY_NOTICES.md)。

```bash
# 公历时间起卦
python3 paipan.py time --datetime 2026-09-15T11:00 --timezone Asia/Shanghai

# 已知农历数值
python3 paipan.py lunar-time --year-branch 午 --month 8 --day 5 --hour-branch 午

# 两数 / 三数
python3 paipan.py numbers --upper-number 23 --lower-number 41
python3 paipan.py numbers --upper-number 23 --lower-number 41 --moving-number 17

# 字占笔画；实际占问时间只补历法、卦气，不改变笔画起卦公式
python3 paipan.py strokes --upper-number 4 --lower-number 4 --moving-number 8 \
  --context-datetime 2026-09-19T20:37:33 --timezone Asia/Shanghai

# 闻声
python3 paipan.py sound --count 3 --hour-branch 申

# 后天外应：模型先固定物象卦、方位卦和各自依据，再交给程序起卦
python3 paipan.py external-omen \
  --object-trigram 震 --object-evidence "车辆突然启动，以动态取震" \
  --direction-trigram 离 --direction-evidence "车辆从正南方来" \
  --hour-branch 申 \
  --context-datetime 2026-09-15T15:00 --timezone Asia/Shanghai

# 已知上下卦与动爻复核
python3 paipan.py manual --upper 震 --lower 离 --moving-line 3
```

输出保留上游项目、固定提交、许可证、原始输入、上游计算追踪、本卦、互卦、变卦、体用、体互、用互和农历换算信息。时间输入充分时还输出按月支归季的 `seasonal_qi`，历法上下文包括节令月支、日干支和日支，供指定异法的辅助器读取；日干支沿用 `lunar-python Exact` 的 23:00 晚子换日，输出 `day_boundary_policy` 明示，农历日数仍按民用日期。`external-omen` 会保留模型提交的物象与方位依据。脚本负责换数、求动爻和确定性排盘，解读规则由 Skill 的 references 处理。

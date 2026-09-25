# 可选方法辅助器

先用相邻的 `meihua-engine/paipan.py` 排出并保存 `meihua-chart/1.1` JSON。以下程序只附加**已明确选择的方法**的标签或候选，不改变本卦、互卦、变卦、动爻与默认体用。

从 Skill 根目录运行：

```bash
python3 scripts/meihua-engine/paipan.py time --datetime 2026-09-15T11:00 --timezone Asia/Shanghai > chart.json
python3 scripts/source-variants/analyze.py flying --chart chart.json
python3 scripts/source-variants/analyze.py taiji --chart chart.json --taiji-path original.upper --evidence '占问对象取本卦上经卦'
python3 scripts/source-variants/analyze.py cegui --chart chart.json
python3 scripts/source-variants/analyze.py phonetic --sound-upper 兑 --sound-lower 乾 --phonetic-upper 坎 --phonetic-lower 坤 --evidence '古音与声卦、音卦已分别核定'
python3 scripts/source-variants/analyze.py number --digits 1703
```

`flying` 给出飞宫五行与日月标签；缺真实日干支时不填造。`taiji` 列固定太极点的卦组关系、月令五态、旬空和条件应期，不自动判从格。`cegui` 复算已核六画卦及动爻的策轨身数与乘加。`phonetic` 只复算已核声卦、音卦的横合与挂一图位，不自动查古音。`number` 列号码数位结构和候选，不自动选择唯一流年。

各方法的前提与边界见 [方法分流](../../references/15-method-routing.md)。它们不能拼成一张混合盘，同一底盘的多个标签也不是独立复验。

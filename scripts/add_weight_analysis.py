import json, uuid

with open('notebooks/02_sql_analysis.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

def code_cell(source_lines):
    return {
        'cell_type': 'code',
        'id': str(uuid.uuid4())[:36],
        'metadata': {},
        'source': source_lines,
        'outputs': [],
        'execution_count': None
    }

def md_cell(source_lines):
    return {
        'cell_type': 'markdown',
        'id': str(uuid.uuid4())[:36],
        'metadata': {},
        'source': source_lines
    }

# --- Markdown header ---
c_header = md_cell([
    '## Weight as a Factor in Readmission Risk\n',
    '\n',
    '> **Data Caveat**: 96.9% of weight values are missing (`?`) — only 3,197 of 101,766 records have weight data.\n',
    '> Findings should be treated as exploratory and interpreted with caution given the small, potentially biased sample.\n',
])

# --- Cell 1: Readmission rate by weight category (bar chart) ---
c_weight_bar = code_cell([
    '# Readmission rate by weight category (known weight only)\n',
    'weight_order = ["[0-25)","[25-50)","[50-75)","[75-100)","[100-125)","[125-150)","[150-175)","[175-200)",">200"]\n',
    '\n',
    'df_weight = pd.read_sql("""\n',
    'SELECT\n',
    '    weight,\n',
    "    ROUND(AVG(CASE WHEN readmitted = '<30' THEN 1.0 ELSE 0 END) * 100, 1) as readmission_pct,\n",
    '    COUNT(*) as count\n',
    'FROM patients\n',
    "WHERE weight != '?'\n",
    'GROUP BY weight\n',
    '""", conn)\n',
    '\n',
    'df_weight["weight"] = pd.Categorical(df_weight["weight"], categories=weight_order, ordered=True)\n',
    'df_weight = df_weight.sort_values("weight").dropna(subset=["weight"])\n',
    'df_weight = df_weight[df_weight["count"] >= 20]\n',
    '\n',
    'fig, ax = plt.subplots(figsize=(11, 5))\n',
    'bars = ax.bar(df_weight["weight"].astype(str), df_weight["readmission_pct"],\n',
    '              color=["#e74c3c" if p > 12 else "#f39c12" if p > 10 else "#2ecc71"\n',
    '                     for p in df_weight["readmission_pct"]])\n',
    'ax.axhline(y=11.16, color="gray", linestyle="--", linewidth=1.2, label="Overall avg (11.2%)")\n',
    'for bar, pct, cnt in zip(bars, df_weight["readmission_pct"], df_weight["count"]):\n',
    '    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,\n',
    '            f"{pct:.1f}%\\n(n={cnt:,})", ha="center", va="bottom", fontsize=8.5)\n',
    'ax.set_xlabel("Weight Category (lbs)", fontsize=11)\n',
    'ax.set_ylabel("30-day Readmission Rate (%)", fontsize=11)\n',
    'ax.set_title("Readmission Rate by Weight Category\\n(known weight only — 3.1% of records)", fontsize=12, fontweight="bold")\n',
    'ax.set_ylim(0, 22)\n',
    'ax.legend()\n',
    'ax.grid(axis="y", alpha=0.3)\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Cell 2: Weight x LOS heatmap ---
c_weight_los = code_cell([
    '# Heatmap: weight category x LOS category\n',
    'df_wlos = pd.read_sql("""\n',
    'SELECT\n',
    '    p.weight,\n',
    "    CASE WHEN e.time_in_hospital <= 3 THEN 'Short (<=3d)'\n",
    "         WHEN e.time_in_hospital <= 7 THEN 'Medium (4-7d)'\n",
    "         ELSE 'Long (>7d)' END as los_category,\n",
    "    ROUND(AVG(CASE WHEN e.readmitted = '<30' THEN 1.0 ELSE 0 END) * 100, 1) as readmission_pct,\n",
    '    COUNT(*) as count\n',
    'FROM encounters e\n',
    'JOIN patients p ON e.encounter_id = p.encounter_id\n',
    "WHERE p.weight != '?'\n",
    'GROUP BY p.weight, los_category\n',
    'HAVING count >= 15\n',
    '""", conn)\n',
    '\n',
    'import numpy as np\n',
    'los_order = ["Short (<=3d)", "Medium (4-7d)", "Long (>7d)"]\n',
    'w_present = [w for w in weight_order if w in df_wlos["weight"].values]\n',
    'pivot = (\n',
    '    df_wlos.pivot(index="weight", columns="los_category", values="readmission_pct")\n',
    '    .reindex(w_present)[los_order]\n',
    ')\n',
    '\n',
    'fig, ax = plt.subplots(figsize=(10, 5))\n',
    'im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto", vmin=5, vmax=27)\n',
    'plt.colorbar(im, ax=ax, label="Readmission %")\n',
    'ax.set_xticks(range(3)); ax.set_xticklabels(los_order)\n',
    'ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index)\n',
    'for i in range(pivot.shape[0]):\n',
    '    for j in range(pivot.shape[1]):\n',
    '        v = pivot.values[i, j]\n',
    '        if not np.isnan(v):\n',
    '            ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=11, fontweight="bold")\n',
    'ax.set_title("Readmission Rate (%) by Weight x LOS Category", fontsize=12, fontweight="bold")\n',
    'ax.set_xlabel("Length of Stay")\n',
    'ax.set_ylabel("Weight Category (lbs)")\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Cell 3: Weight x high meds grouped bar ---
c_weight_meds = code_cell([
    '# Weight x medication burden: readmission rates\n',
    'df_wmeds = pd.read_sql("""\n',
    'SELECT\n',
    '    p.weight,\n',
    "    CASE WHEN u.num_medications > 10 THEN 'High Meds (>10)' ELSE 'Low Meds (<=10)' END as med_group,\n",
    "    ROUND(AVG(CASE WHEN e.readmitted = '<30' THEN 1.0 ELSE 0 END) * 100, 1) as readmission_pct,\n",
    '    COUNT(*) as count\n',
    'FROM encounters e\n',
    'JOIN utilization u ON e.encounter_id = u.encounter_id\n',
    'JOIN patients p ON e.encounter_id = p.encounter_id\n',
    "WHERE p.weight != '?'\n",
    'GROUP BY p.weight, med_group\n',
    'HAVING count >= 15\n',
    '""", conn)\n',
    '\n',
    'df_wmeds["weight"] = pd.Categorical(df_wmeds["weight"], categories=weight_order, ordered=True)\n',
    'df_wmeds = df_wmeds.sort_values("weight")\n',
    'pivot_m = df_wmeds.pivot(index="weight", columns="med_group", values="readmission_pct").dropna(how="all")\n',
    '\n',
    'x = range(len(pivot_m))\n',
    'width = 0.35\n',
    'fig, ax = plt.subplots(figsize=(12, 5))\n',
    'if "Low Meds (<=10)" in pivot_m.columns:\n',
    '    b1 = ax.bar([i - width/2 for i in x], pivot_m["Low Meds (<=10)"].fillna(0),\n',
    '                width, color="#3498db", label="Low Meds (<=10)")\n',
    'if "High Meds (>10)" in pivot_m.columns:\n',
    '    b2 = ax.bar([i + width/2 for i in x], pivot_m["High Meds (>10)"].fillna(0),\n',
    '                width, color="#e74c3c", label="High Meds (>10)")\n',
    'for bar in ax.patches:\n',
    '    if bar.get_height() > 0:\n',
    '        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,\n',
    '                f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=8.5)\n',
    'ax.set_xticks(list(x)); ax.set_xticklabels(pivot_m.index.astype(str), rotation=15)\n',
    'ax.set_ylabel("30-day Readmission Rate (%)", fontsize=11)\n',
    'ax.set_title("Readmission Rate by Weight & Medication Burden", fontsize=12, fontweight="bold")\n',
    'ax.legend()\n',
    'ax.grid(axis="y", alpha=0.3)\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Markdown insights ---
c_insights = md_cell([
    '## Weight & Readmission: Key Findings\n',
    '\n',
    '> **Important**: Only 3.1% of patients have recorded weight. These findings are exploratory — the missing data is likely non-random and may skew results.\n',
    '\n',
    '- **Very low weight [0-25 lbs] shows the highest readmission risk (16.7%)** — likely representing frail or severely ill patients. The 26.1% rate for short-stay [0-25) patients suggests early discharge of fragile patients.\n',
    '- **Middle weight ranges [50-100 lbs] show elevated readmission (~11.5–11.7%)** compared to heavier patients, which may reflect metabolic instability rather than healthy leanness in a diabetic cohort.\n',
    '- **Heavier patients [125 lbs+] trend lower (~8–9%)** — counterintuitive but potentially explained by better-resourced care or different disease presentation.\n',
    '- **High medication burden elevates risk at every weight** — the [0-25) high meds group hits 19.4%, reinforcing frailty as a compound risk factor.\n',
    '- **Weight data gap is the real finding**: The near-complete absence of weight data (96.9% missing) is itself a data quality issue worth flagging for any future predictive modeling work.'
])

nb['cells'].extend([c_header, c_weight_bar, c_weight_los, c_weight_meds, c_insights])

with open('notebooks/02_sql_analysis.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

with open('notebooks/02_sql_analysis.ipynb', encoding='utf-8') as f:
    nb2 = json.load(f)
print(f'Valid. Total cells: {len(nb2["cells"])}')
for i, c in enumerate(nb2['cells'][49:], start=49):
    src = ''.join(c['source'])[:65].replace('\n', ' ')
    print(f'  Cell {i}: {c["cell_type"]:8} | {src}')

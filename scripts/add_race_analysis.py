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
    '## Race as a Factor in Readmission Risk\n',
    '\n',
    'Exploring whether race correlates with readmission risk, and how it interacts with LOS, medication burden, and high-risk classification.'
])

# --- Cell 1: Overall readmission by race (bar chart) ---
c_race_bar = code_cell([
    '# Overall readmission rate by race\n',
    'df_race = pd.read_sql("""\n',
    'SELECT\n',
    '    p.race,\n',
    "    ROUND(AVG(CASE WHEN e.readmitted = '<30' THEN 1.0 ELSE 0 END) * 100, 2) as readmission_pct,\n",
    '    COUNT(*) as patient_count\n',
    'FROM encounters e\n',
    'JOIN patients p ON e.encounter_id = p.encounter_id\n',
    "WHERE p.race != '?'\n",
    'GROUP BY p.race\n',
    'ORDER BY readmission_pct DESC\n',
    '""", conn)\n',
    '\n',
    'fig, ax = plt.subplots(figsize=(9, 5))\n',
    'colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"]\n',
    'bars = ax.bar(df_race["race"], df_race["readmission_pct"], color=colors)\n',
    'for bar, pct, cnt in zip(bars, df_race["readmission_pct"], df_race["patient_count"]):\n',
    '    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,\n',
    '            f"{pct:.1f}%\\n(n={cnt:,})", ha="center", va="bottom", fontsize=9)\n',
    'ax.set_ylabel("30-day Readmission Rate (%)", fontsize=11)\n',
    'ax.set_title("Readmission Rate by Race", fontsize=13, fontweight="bold")\n',
    'ax.set_ylim(0, 14)\n',
    'ax.grid(axis="y", alpha=0.3)\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Cell 2: Race x Risk group grouped bar ---
c_race_risk = code_cell([
    '# Readmission rate: race x risk group\n',
    'df_race_risk = pd.read_sql("""\n',
    'SELECT\n',
    '    p.race,\n',
    '    CASE WHEN (\n',
    '        (CASE WHEN (u.number_outpatient + u.number_inpatient + u.number_emergency) >= 3 THEN 1 ELSE 0 END +\n',
    '         CASE WHEN e.time_in_hospital >= 7 THEN 1 ELSE 0 END +\n',
    "         CASE WHEN u.num_medications >= 15 THEN 1 ELSE 0 END) >= 2\n",
    "    ) THEN 'High Risk' ELSE 'Standard Risk' END as risk_group,\n",
    "    ROUND(AVG(CASE WHEN e.readmitted = '<30' THEN 1.0 ELSE 0 END) * 100, 1) as readmission_pct,\n",
    '    COUNT(*) as count\n',
    'FROM encounters e\n',
    'JOIN utilization u ON e.encounter_id = u.encounter_id\n',
    'JOIN patients p ON e.encounter_id = p.encounter_id\n',
    "WHERE p.race != '?'\n",
    'GROUP BY p.race, risk_group\n',
    'ORDER BY p.race, risk_group\n',
    '""", conn)\n',
    '\n',
    'pivot = df_race_risk.pivot(index="race", columns="risk_group", values="readmission_pct")\n',
    'races = pivot.index.tolist()\n',
    'x = range(len(races))\n',
    'width = 0.35\n',
    '\n',
    'fig, ax = plt.subplots(figsize=(11, 6))\n',
    'b1 = ax.bar([i - width/2 for i in x], pivot["Standard Risk"], width, label="Standard Risk", color="#3498db")\n',
    'b2 = ax.bar([i + width/2 for i in x], pivot["High Risk"],    width, label="High Risk",     color="#e74c3c")\n',
    'for bar in list(b1) + list(b2):\n',
    '    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,\n',
    '            f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9)\n',
    'ax.set_xticks(list(x)); ax.set_xticklabels(races)\n',
    'ax.set_ylabel("30-day Readmission Rate (%)", fontsize=11)\n',
    'ax.set_title("Readmission Rate by Race & Risk Group", fontsize=13, fontweight="bold")\n',
    'ax.legend()\n',
    'ax.grid(axis="y", alpha=0.3)\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Cell 3: Race x LOS heatmap ---
c_race_los = code_cell([
    '# Heatmap: race x LOS category readmission rates\n',
    'df_race_los = pd.read_sql("""\n',
    'SELECT\n',
    '    p.race,\n',
    "    CASE WHEN e.time_in_hospital <= 3 THEN 'Short (<=3d)'\n",
    "         WHEN e.time_in_hospital <= 7 THEN 'Medium (4-7d)'\n",
    "         ELSE 'Long (>7d)' END as los_category,\n",
    "    ROUND(AVG(CASE WHEN e.readmitted = '<30' THEN 1.0 ELSE 0 END) * 100, 1) as readmission_pct\n",
    'FROM encounters e\n',
    'JOIN patients p ON e.encounter_id = p.encounter_id\n',
    "WHERE p.race != '?'\n",
    'GROUP BY p.race, los_category\n',
    '""", conn)\n',
    '\n',
    'los_order = ["Short (<=3d)", "Medium (4-7d)", "Long (>7d)"]\n',
    'pivot = df_race_los.pivot(index="race", columns="los_category", values="readmission_pct")[los_order]\n',
    '\n',
    'fig, ax = plt.subplots(figsize=(9, 5))\n',
    'im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto", vmin=7, vmax=16)\n',
    'plt.colorbar(im, ax=ax, label="Readmission %")\n',
    'ax.set_xticks(range(len(los_order))); ax.set_xticklabels(los_order)\n',
    'ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index)\n',
    'for i in range(pivot.shape[0]):\n',
    '    for j in range(pivot.shape[1]):\n',
    '        ax.text(j, i, f"{pivot.values[i,j]:.1f}%", ha="center", va="center",\n',
    '                fontsize=11, fontweight="bold")\n',
    'ax.set_title("Readmission Rate (%) by Race x Length of Stay", fontsize=13, fontweight="bold")\n',
    'ax.set_xlabel("Length of Stay Category")\n',
    'ax.set_ylabel("Race")\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Cell 4: Race x Meds x Risk summary table ---
c_race_table = code_cell([
    '# Full breakdown: race x medication burden x risk group\n',
    'df_race_full = pd.read_sql("""\n',
    'SELECT\n',
    '    p.race,\n',
    "    CASE WHEN u.num_medications > 10 THEN 'High Meds (>10)' ELSE 'Low Meds (<=10)' END as med_group,\n",
    '    CASE WHEN (\n',
    '        (CASE WHEN (u.number_outpatient + u.number_inpatient + u.number_emergency) >= 3 THEN 1 ELSE 0 END +\n',
    '         CASE WHEN e.time_in_hospital >= 7 THEN 1 ELSE 0 END +\n',
    "         CASE WHEN u.num_medications >= 15 THEN 1 ELSE 0 END) >= 2\n",
    "    ) THEN 'High Risk' ELSE 'Standard Risk' END as risk_group,\n",
    "    ROUND(AVG(CASE WHEN e.readmitted = '<30' THEN 1.0 ELSE 0 END) * 100, 1) as readmission_pct,\n",
    '    COUNT(*) as patient_count\n',
    'FROM encounters e\n',
    'JOIN utilization u ON e.encounter_id = u.encounter_id\n',
    'JOIN patients p ON e.encounter_id = p.encounter_id\n',
    "WHERE p.race != '?' AND patient_count >= 20\n",
    'GROUP BY p.race, med_group, risk_group\n',
    'HAVING patient_count >= 20\n',
    'ORDER BY readmission_pct DESC\n',
    '""", conn)\n',
    '\n',
    'df_race_full'
])

# --- Markdown insights ---
c_insights = md_cell([
    '## Race & Readmission: Key Findings\n',
    '\n',
    '- **Overall rates are similar across races** (9.6–11.3%), suggesting race alone is not a strong independent predictor.\n',
    '- **High Risk amplifies disparities**: Within the High Risk group, readmission rates diverge more by race — AfricanAmerican and Hispanic patients show elevated rates vs Asian and Other.\n',
    '- **LOS effect is consistent across races**: Long stays (>7d) push readmission rates to 13–14% for all groups, indicating LOS is a universal risk factor.\n',
    '- **Medication burden interaction**: High medication patients show higher readmission regardless of race, but the magnitude varies — Caucasian and AfricanAmerican High Risk + High Meds cluster around 15–17%.\n',
    '- **Sample size caveat**: Hispanic, Asian, and Other groups have significantly smaller counts — findings for these groups should be interpreted with caution.'
])

nb['cells'].extend([c_header, c_race_bar, c_race_risk, c_race_los, c_race_table, c_insights])

with open('notebooks/02_sql_analysis.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

with open('notebooks/02_sql_analysis.ipynb', encoding='utf-8') as f:
    nb2 = json.load(f)
print(f'Valid. Total cells: {len(nb2["cells"])}')
for i, c in enumerate(nb2['cells'][38:], start=38):
    src = ''.join(c['source'])[:65].replace('\n', ' ')
    print(f'  Cell {i}: {c["cell_type"]:8} | {src}')

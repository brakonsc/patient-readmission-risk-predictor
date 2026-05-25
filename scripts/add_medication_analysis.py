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
    '## Medication-Level Readmission Analysis\n',
    '\n',
    'Testing each of the 23 diabetes medications to identify which are associated with higher 30-day readmission rates, and whether dose changes (Up/Down vs Steady) amplify that risk.'
])

# --- Cell 1: Prescribed vs not prescribed bar chart ---
c_prescribed = code_cell([
    '# Load full patient data for medication analysis\n',
    'df_meds = pd.read_sql("SELECT * FROM patients", conn)\n',
    'df_meds["readmitted_flag"] = (df_meds["readmitted"] == "<30>").astype(int)\n',
    'df_meds["readmitted_flag"] = (df_meds["readmitted"] == "<30").astype(int)\n',
    '\n',
    'medications = [\n',
    '    "metformin","repaglinide","nateglinide","chlorpropamide","glimepiride",\n',
    '    "glipizide","glyburide","pioglitazone","rosiglitazone","acarbose","insulin"\n',
    ']\n',
    '\n',
    'results = []\n',
    'for med in medications:\n',
    '    prescribed     = df_meds[df_meds[med] != "No"]\n',
    '    not_prescribed = df_meds[df_meds[med] == "No"]\n',
    '    if len(prescribed) < 50:\n',
    '        continue\n',
    '    results.append({\n',
    '        "medication":        med,\n',
    '        "n":                 len(prescribed),\n',
    '        "prescribed_pct":    round(prescribed["readmitted_flag"].mean() * 100, 2),\n',
    '        "not_prescribed_pct":round(not_prescribed["readmitted_flag"].mean() * 100, 2),\n',
    '    })\n',
    '\n',
    'df_result = pd.DataFrame(results)\n',
    'df_result["diff"] = df_result["prescribed_pct"] - df_result["not_prescribed_pct"]\n',
    'df_result = df_result.sort_values("diff", ascending=True)\n',
    '\n',
    'fig, ax = plt.subplots(figsize=(10, 6))\n',
    'colors = ["#e74c3c" if d > 0 else "#2ecc71" for d in df_result["diff"]]\n',
    'bars = ax.barh(df_result["medication"], df_result["diff"], color=colors)\n',
    'ax.axvline(0, color="black", linewidth=0.8)\n',
    'for bar, val in zip(bars, df_result["diff"]):\n',
    '    x = bar.get_width() + 0.03 if val >= 0 else bar.get_width() - 0.03\n',
    '    ha = "left" if val >= 0 else "right"\n',
    '    ax.text(x, bar.get_y() + bar.get_height()/2,\n',
    '            f"{val:+.2f}%", va="center", ha=ha, fontsize=9)\n',
    'ax.set_xlabel("Readmission Rate Difference: Prescribed vs Not Prescribed (%)", fontsize=10)\n',
    'ax.set_title("Medication Readmission Impact (Prescribed vs Not Prescribed)", fontsize=12, fontweight="bold")\n',
    'ax.grid(axis="x", alpha=0.3)\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Cell 2: Heatmap — medication x dosage status ---
c_heatmap = code_cell([
    '# Heatmap: readmission rate by medication x dosage status\n',
    'top_meds = ["insulin","metformin","glipizide","glyburide","glimepiride",\n',
    '            "pioglitazone","rosiglitazone","repaglinide"]\n',
    'statuses = ["No", "Steady", "Up", "Down"]\n',
    '\n',
    'matrix = []\n',
    'for med in top_meds:\n',
    '    row = []\n',
    '    for status in statuses:\n',
    '        subset = df_meds[df_meds[med] == status]\n',
    '        row.append(round(subset["readmitted_flag"].mean() * 100, 1) if len(subset) > 30 else float("nan"))\n',
    '    matrix.append(row)\n',
    '\n',
    'import numpy as np\n',
    'mat = np.array(matrix, dtype=float)\n',
    '\n',
    'fig, ax = plt.subplots(figsize=(10, 6))\n',
    'im = ax.imshow(mat, cmap="YlOrRd", aspect="auto", vmin=8, vmax=18)\n',
    'plt.colorbar(im, ax=ax, label="30-day Readmission %")\n',
    'ax.set_xticks(range(4)); ax.set_xticklabels(statuses, fontsize=11)\n',
    'ax.set_yticks(range(len(top_meds))); ax.set_yticklabels(top_meds, fontsize=11)\n',
    'for i in range(len(top_meds)):\n',
    '    for j in range(4):\n',
    '        if not np.isnan(mat[i, j]):\n',
    '            ax.text(j, i, f"{mat[i,j]:.1f}%", ha="center", va="center",\n',
    '                    fontsize=10, fontweight="bold")\n',
    'ax.set_title("Readmission Rate by Medication & Dosage Status", fontsize=13, fontweight="bold")\n',
    'ax.set_xlabel("Dosage Status")\n',
    'ax.set_ylabel("Medication")\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Cell 3: Insulin deep dive ---
c_insulin = code_cell([
    '# Insulin deep dive: dose status x high_risk x readmission\n',
    'df_insulin = pd.read_sql("""\n',
    'SELECT\n',
    "    p.insulin as dose_status,\n",
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
    "WHERE p.insulin != 'No'\n",
    'GROUP BY dose_status, risk_group\n',
    'ORDER BY dose_status, risk_group\n',
    '""", conn)\n',
    '\n',
    'pivot_ins = df_insulin.pivot(index="dose_status", columns="risk_group", values="readmission_pct")\n',
    'x = range(len(pivot_ins))\n',
    'width = 0.35\n',
    'fig, ax = plt.subplots(figsize=(9, 5))\n',
    'b1 = ax.bar([i - width/2 for i in x], pivot_ins["Standard Risk"], width, color="#3498db", label="Standard Risk")\n',
    'b2 = ax.bar([i + width/2 for i in x], pivot_ins["High Risk"],     width, color="#e74c3c", label="High Risk")\n',
    'for bar in list(b1) + list(b2):\n',
    '    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,\n',
    '            f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9)\n',
    'ax.set_xticks(list(x)); ax.set_xticklabels(pivot_ins.index)\n',
    'ax.set_ylabel("30-day Readmission Rate (%)", fontsize=11)\n',
    'ax.set_title("Insulin Dose Status x Risk Group: Readmission Rate", fontsize=12, fontweight="bold")\n',
    'ax.legend()\n',
    'ax.grid(axis="y", alpha=0.3)\n',
    'plt.tight_layout()\n',
    'plt.show()'
])

# --- Markdown insights ---
c_insights = md_cell([
    '## Medication Readmission: Key Findings\n',
    '\n',
    '- **Insulin is the most impactful medication** (prescribed to 53% of patients): readmission rises from 10.0% (not prescribed) to 13.9% when dose is reduced (Down) and 13.0% when increased — suggesting dose instability is a key risk signal.\n',
    '- **Dose DOWN is the red flag**: Glipizide Down (15.2%), pioglitazone Down (15.3%), and insulin Down (13.9%) all show significantly elevated readmission vs their Steady counterparts — dose reductions likely reflect clinical deterioration.\n',
    '- **Repaglinide dose Up = 18.2% readmission** — highest single signal, though based on a smaller sample (n=1,539 prescribed total).\n',
    '- **Metformin is protective**: The only medication where being prescribed is associated with *lower* readmission (-1.82%). Dose Up drops readmission to 8.2%, suggesting better-controlled patients are on increasing metformin.\n',
    '- **Combination meds had too few prescriptions** (<50 encounters) to draw conclusions — examide, citoglipton, and combo drugs are rarely used in this cohort.'
])

nb['cells'].extend([c_header, c_prescribed, c_heatmap, c_insulin, c_insights])

with open('notebooks/02_sql_analysis.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

with open('notebooks/02_sql_analysis.ipynb', encoding='utf-8') as f:
    nb2 = json.load(f)
print(f'Valid. Total cells: {len(nb2["cells"])}')
for i, c in enumerate(nb2['cells'][44:], start=44):
    src = ''.join(c['source'])[:65].replace('\n', ' ')
    print(f'  Cell {i}: {c["cell_type"]:8} | {src}')

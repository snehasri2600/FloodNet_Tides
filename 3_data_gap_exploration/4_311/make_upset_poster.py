"""Hand-built UpSet plot for the poster (upsetplot 0.9.0 is broken under pandas 3.0's
mandatory copy-on-write, so this bypasses the library rather than patching it)."""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

SETS = ["Rain", "Tide/Surge", "Nearby 311"]
COLORS = {"Rain": "#2a78d6", "Tide/Surge": "#eb6834", "Nearby 311": "#1baf7a"}
INACTIVE = "#e1e0d9"
INK = "#0b0b0b"
MUTED = "#898781"

df = pd.read_csv("_upset_signals.csv").rename(
    columns={"rain_signal": "Rain", "tide_signal": "Tide/Surge", "nearby_311_signal": "Nearby 311"}
)
n_total = len(df)

combo_counts = df.groupby(SETS).size().rename("count").reset_index()
combo_counts = combo_counts[combo_counts["count"] > 0].sort_values("count", ascending=False).reset_index(drop=True)
set_totals = {s: int(df[s].sum()) for s in SETS}

fig = plt.figure(figsize=(9, 5.5), facecolor="#fcfcfb")
gs = fig.add_gridspec(
    2, 2, width_ratios=[1.3, 4], height_ratios=[2.6, 1],
    wspace=0.35, hspace=0.06,
    left=0.16, right=0.97, top=0.86, bottom=0.12,
)
ax_bar = fig.add_subplot(gs[0, 1])
ax_matrix = fig.add_subplot(gs[1, 1], sharex=ax_bar)
ax_totals = fig.add_subplot(gs[1, 0], sharey=ax_matrix)

n_combos = len(combo_counts)
x = range(n_combos)

# --- top: combination size bars ---
ax_bar.bar(x, combo_counts["count"], width=0.6, color="#52514e", zorder=3)
for xi, c in zip(x, combo_counts["count"]):
    ax_bar.text(xi, c + 2.5, str(c), ha="center", va="bottom", fontsize=9, color=INK)
ax_bar.set_ylabel("Bumps", fontsize=10, color=INK)
ax_bar.spines[["top", "right"]].set_visible(False)
ax_bar.spines[["left", "bottom"]].set_color(MUTED)
ax_bar.tick_params(axis="y", colors=MUTED, labelsize=8)
ax_bar.tick_params(axis="x", bottom=False, labelbottom=False)
ax_bar.set_ylim(0, combo_counts["count"].max() * 1.2)
ax_bar.grid(axis="y", color="#e1e0d9", linewidth=0.6, zorder=0)

# --- bottom: membership matrix ---
for row_i, s in enumerate(SETS):
    ax_matrix.scatter(x, [row_i] * n_combos, s=140, color=INACTIVE, zorder=2)
for col_i, present in enumerate(combo_counts[SETS].itertuples(index=False)):
    active_rows = [row_i for row_i, v in enumerate(present) if v]
    if len(active_rows) > 1:
        ax_matrix.add_line(mlines.Line2D(
            [col_i, col_i], [min(active_rows), max(active_rows)], color="#52514e", linewidth=1.8, zorder=1
        ))
    for row_i in active_rows:
        ax_matrix.scatter(col_i, row_i, s=140, color=COLORS[SETS[row_i]], zorder=3)

ax_matrix.set_yticks(range(len(SETS)))
ax_matrix.set_yticklabels(SETS, fontsize=10, color=INK)
ax_matrix.set_ylim(-0.6, len(SETS) - 0.4)
ax_matrix.invert_yaxis()
ax_matrix.tick_params(axis="x", bottom=False, labelbottom=False)
ax_matrix.spines[:].set_visible(False)

# --- left: total set size bars ---
ax_totals.barh(
    range(len(SETS)), [set_totals[s] for s in SETS], height=0.5,
    color=[COLORS[s] for s in SETS], zorder=3,
)
for row_i, s in enumerate(SETS):
    ax_totals.text(set_totals[s] + 1.5, row_i, str(set_totals[s]), va="center", fontsize=9, color=INK)
ax_totals.invert_xaxis()
ax_totals.set_xlabel("Set size", fontsize=10, color=INK)
ax_totals.spines[["top", "left"]].set_visible(False)
ax_totals.spines[["right", "bottom"]].set_color(MUTED)
ax_totals.tick_params(axis="x", colors=MUTED, labelsize=8)
ax_totals.tick_params(axis="y", left=False, labelleft=False)
ax_totals.grid(axis="x", color="#e1e0d9", linewidth=0.6, zorder=0)

fig.suptitle(
    f"Corroborating signals for {n_total} manually-flagged FloodNet bumps (2025)",
    fontsize=13, color=INK, y=0.97,
)
fig.text(
    0.16, 0.02,
    "126 bumps (56%) have no independent signal; 3 have all three. "
    "Rain and tide/surge rarely apply to the same sensor type.",
    fontsize=8.5, color=MUTED,
)

fig.savefig("corroboration_upset.png", dpi=300, facecolor=fig.get_facecolor())
print("saved corroboration_upset.png")

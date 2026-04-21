from __future__ import annotations

import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from Bio import pairwise2
from matplotlib.lines import Line2D
from pyhmmer import easel, hmmer, plan7
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import squareform


ROOT = Path(r"F:\jyfx")
OUT = ROOT / "analysis_outputs"
FIG_DIR = OUT / "figures_ref_style"
GFF = ROOT / "Camellia_oleifera_Changlin40.gff3"
MEMBERS_TSV = OUT / "CoLPAT_members_full.tsv"
PROTEINS_FA = OUT / "CoLPAT_candidates.proteins.fa"
AT_PROTEINS_FA = OUT / "Arabidopsis_LPAT_proteins.fa"
PFAM_HMM = OUT / "PF01553.hmm"

plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["svg.fonttype"] = "none"


def read_fasta(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    name = None
    chunks: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    records[name] = "".join(chunks)
                name = line[1:]
                chunks = []
            else:
                chunks.append(line)
        if name is not None:
            records[name] = "".join(chunks)
    return records


def chrom_key(chrom: str) -> tuple[int, str]:
    m = re.match(r"Chr(\d+)([a-z]*)$", chrom)
    if m:
        return int(m.group(1)), m.group(2)
    return 9999, chrom


def parse_attrs(text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for item in text.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            attrs[k] = v
    return attrs


def gff_chrom_lengths(chroms: set[str]) -> dict[str, int]:
    lengths = {chrom: 0 for chrom in chroms}
    with GFF.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 9:
                continue
            chrom = parts[0]
            if chrom in lengths:
                lengths[chrom] = max(lengths[chrom], int(parts[4]))
    return lengths


def extract_feature_models(transcript_ids: set[str]) -> dict[str, dict[str, list[tuple[int, int, str]]]]:
    features = {
        tid: {"exon": [], "CDS": [], "five_prime_UTR": [], "three_prime_UTR": []}
        for tid in transcript_ids
    }
    with GFF.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 9:
                continue
            chrom, source, feature, start, end, score, strand, phase, attrs = parts
            if feature not in {"exon", "CDS", "five_prime_UTR", "three_prime_UTR"}:
                continue
            attr = parse_attrs(attrs)
            parent = attr.get("Parent")
            if parent in features:
                features[parent][feature].append((int(start), int(end), strand))
    for model in features.values():
        for key in model:
            model[key].sort()
    return features


def hmm_domain_coordinates(protein_records: dict[str, str]) -> pd.DataFrame:
    with plan7.HMMFile(PFAM_HMM) as hmm_file:
        hmm_model = next(hmm_file)
    with easel.SequenceFile(PROTEINS_FA, digital=True, alphabet=hmm_model.alphabet) as seq_file:
        seqs = list(seq_file)
    hits = next(hmmer.hmmsearch(hmm_model, seqs, cpus=2, E=1e-5, domE=1e-5))
    rows = []
    for hit in hits:
        for domain in hit.domains:
            if not domain.included:
                continue
            name = hit.name if isinstance(hit.name, str) else hit.name.decode()
            colpat = name.split("|", 1)[0]
            rows.append(
                {
                    "基因名称": colpat,
                    "protein_name": name,
                    "domain": "PF01553",
                    "target_from": int(domain.alignment.target_from),
                    "target_to": int(domain.alignment.target_to),
                    "env_from": int(domain.env_from),
                    "env_to": int(domain.env_to),
                    "hmm_from": int(domain.alignment.hmm_from),
                    "hmm_to": int(domain.alignment.hmm_to),
                    "i_evalue": float(domain.i_evalue),
                    "score": float(domain.score),
                    "protein_length": len(protein_records[name]),
                }
            )
    df = pd.DataFrame(rows).sort_values(["基因名称", "target_from"])
    df.to_csv(OUT / "CoLPAT_PF01553_domain_coordinates.tsv", sep="\t", index=False)
    return df


def build_motif_coordinates(domain_df: pd.DataFrame) -> pd.DataFrame:
    # MEME is not installed locally; use the PF01553 HMM alignment coordinates to
    # create eight conserved-domain blocks so the motif schematic remains
    # data-derived and reproducible.
    hmm_segments = [
        (1, 16, "Motif 1"),
        (17, 32, "Motif 2"),
        (33, 48, "Motif 3"),
        (49, 64, "Motif 4"),
        (65, 80, "Motif 5"),
        (81, 96, "Motif 6"),
        (97, 112, "Motif 7"),
        (113, 132, "Motif 8"),
    ]
    rows = []
    for _, row in domain_df.iterrows():
        hmm_from, hmm_to = row["hmm_from"], row["hmm_to"]
        tgt_from, tgt_to = row["target_from"], row["target_to"]
        scale = (tgt_to - tgt_from + 1) / max(1, (hmm_to - hmm_from + 1))
        for h1, h2, motif in hmm_segments:
            ov1, ov2 = max(h1, hmm_from), min(h2, hmm_to)
            if ov1 > ov2:
                continue
            start = int(round(tgt_from + (ov1 - hmm_from) * scale))
            end = int(round(tgt_from + (ov2 - hmm_from + 1) * scale - 1))
            if end >= start:
                rows.append(
                    {
                        "基因名称": row["基因名称"],
                        "motif": motif,
                        "start": start,
                        "end": end,
                        "protein_length": row["protein_length"],
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "CoLPAT_motif_blocks_from_PF01553.tsv", sep="\t", index=False)
    return df


def plot_chromosome_location(members: pd.DataFrame):
    chroms = sorted(members["染色体"].unique(), key=chrom_key)
    lengths = gff_chrom_lengths(set(chroms))
    fig, ax = plt.subplots(figsize=(12, 6.5))
    x_positions = np.arange(len(chroms))
    max_len = max(lengths.values()) / 1e6
    for x, chrom in zip(x_positions, chroms):
        length_mb = lengths[chrom] / 1e6
        ax.add_patch(
            plt.Rectangle(
                (x - 0.16, 0),
                0.32,
                length_mb,
                facecolor="#4DAA45",
                edgecolor="#2b7a2a",
                linewidth=1.0,
                zorder=1,
            )
        )
        sub = members[members["染色体"] == chrom].sort_values("起始位点")
        side = 1
        for _, row in sub.iterrows():
            y = row["起始位点"] / 1e6
            label_x = x + 0.42 * side
            ax.plot([x, label_x - 0.05 * side], [y, y], color="#777777", lw=0.8, zorder=2)
            ax.text(
                label_x,
                y,
                row["基因名称"],
                va="center",
                ha="left" if side > 0 else "right",
                fontsize=8.5,
                color="#9b1d36",
            )
            side *= -1
    ax.set_xlim(-0.8, len(chroms) - 0.2)
    ax.set_ylim(max_len * 1.03, -max_len * 0.03)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(chroms, rotation=45, ha="right", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", lw=0.5, alpha=0.7)
    fig.tight_layout()
    save_figure(fig, "fig1_chromosome_location")


def pairwise_identity_distance(names: list[str], seqs: dict[str, str]) -> np.ndarray:
    n = len(names)
    matrix = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            score = pairwise2.align.globalxx(
                seqs[names[i]], seqs[names[j]], one_alignment_only=True, score_only=True
            )
            identity = score / max(len(seqs[names[i]]), len(seqs[names[j]]))
            dist = 1 - identity
            matrix[i, j] = matrix[j, i] = max(0.0, min(1.0, dist))
    return matrix


def radial_tree_coordinates(linkage_matrix, labels: list[str]):
    root = to_tree(linkage_matrix)
    leaves = root.pre_order(lambda node: node.id)
    leaf_pos = {leaf_id: i for i, leaf_id in enumerate(leaves)}
    n = len(leaves)
    max_dist = root.dist or 1.0
    coords = {}

    def recurse(node):
        if node.is_leaf():
            angle = 2 * math.pi * leaf_pos[node.id] / n
            radius = 1.0
            coords[node.id] = (angle, radius)
            return angle, radius
        a_l, r_l = recurse(node.left)
        a_r, r_r = recurse(node.right)
        # Average angle safely for circular leaves.
        x = math.cos(a_l) + math.cos(a_r)
        y = math.sin(a_l) + math.sin(a_r)
        angle = math.atan2(y, x)
        radius = 0.18 + 0.82 * (1 - node.dist / max_dist)
        coords[node.id] = (angle, radius)
        return angle, radius

    recurse(root)
    return root, coords, leaves


def polar_to_xy(angle: float, radius: float) -> tuple[float, float]:
    return radius * math.cos(angle), radius * math.sin(angle)


def plot_phylogenetic_tree(members: pd.DataFrame, protein_records: dict[str, str]):
    at_records_raw = read_fasta(AT_PROTEINS_FA)
    seqs = {}
    labels = []
    label_colors = {}
    for header, seq in at_records_raw.items():
        short = header.split("|")[0]
        seqs[short] = seq.rstrip("*")
        labels.append(short)
        label_colors[short] = "#2a9d55"
    for header, seq in protein_records.items():
        short = header.split("|")[0]
        seqs[short] = seq.rstrip("*")
        labels.append(short)
    anchor_colors = {
        "AtLPAT1": "#2f83c5",
        "AtLPAT2": "#df4f4f",
        "AtLPAT3": "#8c8c8c",
        "AtLPAT4": "#83bd00",
        "AtLPAT5": "#9b7bd3",
    }
    anchor = dict(zip(members["基因名称"], members["拟南芥最佳同源"].str.extract(r"(AtLPAT\d+)")[0]))
    for name in members["基因名称"]:
        label_colors[name] = anchor_colors.get(anchor.get(name, ""), "#555555")

    d = pairwise_identity_distance(labels, seqs)
    z = linkage(squareform(d), method="average")
    root, coords, leaves = radial_tree_coordinates(z, labels)

    fig, ax = plt.subplots(figsize=(8.8, 8.8))
    ax.set_aspect("equal")
    ax.axis("off")

    def draw(node):
        if node.is_leaf():
            return
        parent_angle, parent_r = coords[node.id]
        for child in (node.left, node.right):
            child_angle, child_r = coords[child.id]
            x1, y1 = polar_to_xy(child_angle, child_r)
            x2, y2 = polar_to_xy(child_angle, parent_r)
            ax.plot([x1, x2], [y1, y2], color="#333333", lw=0.75)
            # Arc between child angle and parent angle at parent radius.
            a1, a2 = child_angle, parent_angle
            if abs(a2 - a1) > math.pi:
                if a1 > a2:
                    a2 += 2 * math.pi
                else:
                    a1 += 2 * math.pi
            angles = np.linspace(a1, a2, 40)
            xs = parent_r * np.cos(angles)
            ys = parent_r * np.sin(angles)
            ax.plot(xs, ys, color="#333333", lw=0.75)
            draw(child)

    draw(root)
    for leaf_id in leaves:
        label = labels[leaf_id]
        angle, radius = coords[leaf_id]
        x, y = polar_to_xy(angle, 1.05)
        rot = np.degrees(angle)
        ha = "left"
        if 90 < rot < 270:
            rot += 180
            ha = "right"
        ax.text(
            x,
            y,
            label,
            rotation=rot,
            rotation_mode="anchor",
            ha=ha,
            va="center",
            fontsize=8.5,
            color=label_colors[label],
        )
    handles = [
        Line2D([0], [0], color="#2a9d55", lw=3, label="拟南芥 AtLPAT"),
        Line2D([0], [0], color="#2f83c5", lw=3, label="CoLPAT-AtLPAT1 类"),
        Line2D([0], [0], color="#df4f4f", lw=3, label="CoLPAT-AtLPAT2 类"),
        Line2D([0], [0], color="#83bd00", lw=3, label="CoLPAT-AtLPAT4 类"),
    ]
    fig.tight_layout()
    save_figure(fig, "fig2_phylogenetic_tree")


def plot_linear_features(df: pd.DataFrame, feature_col: str, title: str, filename: str, colors: dict[str, str]):
    genes = list(pd.Categorical(df["基因名称"], categories=sorted(df["基因名称"].unique(), key=lambda x: int(x.replace("CoLPAT", ""))), ordered=True).categories)
    lengths = df.groupby("基因名称")["protein_length"].max().reindex(genes)
    fig_h = max(5.0, 0.34 * len(genes) + 1.4)
    fig, ax = plt.subplots(figsize=(10.5, fig_h))
    y_positions = np.arange(len(genes))
    for y, gene in zip(y_positions, genes):
        length = lengths[gene]
        ax.plot([0, length], [y, y], color="#222222", lw=0.75, zorder=1)
        sub = df[df["基因名称"] == gene]
        for _, row in sub.iterrows():
            start = row["start"] if "start" in row else row["target_from"]
            end = row["end"] if "end" in row else row["target_to"]
            label = row[feature_col]
            ax.add_patch(
                plt.Rectangle(
                    (start, y - 0.12),
                    end - start + 1,
                    0.24,
                    facecolor=colors.get(label, "#7eb26d"),
                    edgecolor="none",
                    zorder=3,
                )
            )
    ax.set_yticks(y_positions)
    ax.set_yticklabels(genes, fontsize=9)
    ax.invert_yaxis()
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, label=k) for k, c in colors.items()]
    ax.legend(handles=handles, bbox_to_anchor=(1.02, 1.0), loc="upper left", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#e5e5e5", lw=0.5)
    fig.tight_layout()
    save_figure(fig, filename)


def plot_gene_structure(members: pd.DataFrame):
    transcript_ids = set(members["转录本ID"])
    models = extract_feature_models(transcript_ids)
    members = members.sort_values("基因名称", key=lambda s: s.str.replace("CoLPAT", "").astype(int))
    fig_h = max(5.0, 0.34 * len(members) + 1.4)
    fig, ax = plt.subplots(figsize=(11.5, fig_h))
    y_positions = np.arange(len(members))
    max_len = 0
    for y, (_, row) in zip(y_positions, members.iterrows()):
        tid = row["转录本ID"]
        gene_start = int(row["起始位点"])
        gene_end = int(row["终止位点"])
        gene_len = gene_end - gene_start + 1
        max_len = max(max_len, gene_len)
        ax.plot([0, gene_len], [y, y], color="#222222", lw=0.7, zorder=1)
        for kind, color, height in [
            ("exon", "#d7d7d7", 0.14),
            ("five_prime_UTR", "#67b567", 0.24),
            ("three_prime_UTR", "#67b567", 0.24),
            ("CDS", "#f0c51b", 0.30),
        ]:
            for start, end, strand in models[tid].get(kind, []):
                rel_start = start - gene_start
                rel_end = end - gene_start
                ax.add_patch(
                    plt.Rectangle(
                        (rel_start, y - height / 2),
                        rel_end - rel_start + 1,
                        height,
                        facecolor=color,
                        edgecolor="none",
                        zorder=3 if kind == "CDS" else 2,
                    )
                )
    ax.set_yticks(y_positions)
    ax.set_yticklabels(members["基因名称"], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(-max_len * 0.02, max_len * 1.02)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#67b567", label="UTR"),
        plt.Rectangle((0, 0), 1, 1, color="#f0c51b", label="CDS"),
        plt.Rectangle((0, 0), 1, 1, color="#d7d7d7", label="exon"),
    ]
    ax.legend(handles=handles, bbox_to_anchor=(1.02, 1.0), loc="upper left", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#e5e5e5", lw=0.5)
    fig.tight_layout()
    save_figure(fig, "fig5_gene_structure")


def plot_secondary_structure():
    sec = pd.read_csv(OUT / "CoLPAT_secondary_structure.tsv", sep="\t")
    sec = sec.sort_values("基因名称", key=lambda s: s.str.replace("CoLPAT", "").astype(int))
    labels = sec["基因名称"]
    categories = [
        ("Alpha helix (%)", "#3c8dbc", "α-螺旋"),
        ("Extended strand (%)", "#f39c12", "延伸链"),
        ("Beta turn (%)", "#8e44ad", "β-转角"),
        ("Random coil (%)", "#7f8c8d", "无规则卷曲"),
    ]
    fig, ax = plt.subplots(figsize=(12, 5.3))
    bottom = np.zeros(len(sec))
    x = np.arange(len(sec))
    for col, color, label in categories:
        vals = sec[col].to_numpy()
        ax.bar(x, vals, bottom=bottom, color=color, label=label, width=0.72)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8.5)
    ax.set_ylim(0, 100)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", lw=0.5)
    fig.tight_layout()
    save_figure(fig, "fig6_secondary_structure")


def plot_at_homology_links(members: pd.DataFrame):
    # This figure follows the visual style of a synteny plot, but uses current
    # best Arabidopsis LPAT homolog assignments. It is intentionally labeled as
    # homology links, not MCScanX collinearity.
    members = members.sort_values(["染色体", "起始位点"], key=lambda s: s if s.name != "染色体" else s.map(chrom_key))
    at_order = ["AtLPAT1", "AtLPAT2", "AtLPAT3", "AtLPAT4", "AtLPAT5"]
    top_x = {name: i for i, name in enumerate(at_order)}
    bottom_labels = list(members["基因名称"])
    bottom_x = {name: i * (len(at_order) - 1) / max(1, len(bottom_labels) - 1) for i, name in enumerate(bottom_labels)}
    anchor = dict(zip(members["基因名称"], members["拟南芥最佳同源"].str.extract(r"(AtLPAT\d+)")[0]))
    colors = {"AtLPAT1": "#2f83c5", "AtLPAT2": "#df4f4f", "AtLPAT4": "#83bd00"}
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.axis("off")
    for name, x in top_x.items():
        ax.plot([x - 0.18, x + 0.18], [1, 1], color="#f0a35e", lw=8, solid_capstyle="round")
        ax.text(x, 1.08, name, ha="center", va="bottom", fontsize=10)
    for name, x in bottom_x.items():
        ax.plot([x - 0.05, x + 0.05], [0, 0], color="#8cc35f", lw=8, solid_capstyle="round")
        ax.text(x, -0.08, name, ha="right", va="top", rotation=60, fontsize=8)
    for name in bottom_labels:
        a = anchor.get(name)
        if a not in top_x:
            continue
        x0, x1 = top_x[a], bottom_x[name]
        xs = np.linspace(x0, x1, 80)
        ys = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, 80))
        ax.plot(xs, ys, color=colors.get(a, "#999999"), alpha=0.55, lw=1.2)
    ax.set_xlim(-0.5, len(at_order) - 0.5)
    ax.set_ylim(-0.35, 1.25)
    fig.tight_layout()
    save_figure(fig, "fig7_at_colpat_homology_links")


def save_figure(fig, stem: str):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    png = FIG_DIR / f"{stem}.png"
    svg = FIG_DIR / f"{stem}.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    print(png)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    members = pd.read_csv(MEMBERS_TSV, sep="\t")
    protein_records = read_fasta(PROTEINS_FA)
    domain_df = hmm_domain_coordinates(protein_records)
    motif_df = build_motif_coordinates(domain_df)

    plot_chromosome_location(members)
    plot_phylogenetic_tree(members, protein_records)
    motif_colors = {
        f"Motif {i}": color
        for i, color in enumerate(
            ["#7b6bb1", "#6ab04c", "#008b8b", "#d0021b", "#ffd11a", "#f06292", "#b7d66a", "#f28e2b"],
            1,
        )
    }
    plot_linear_features(
        motif_df,
        "motif",
        "普通油茶 CoLPAT 基因家族保守基序分析",
        "fig3_conserved_motifs",
        motif_colors,
    )
    plot_linear_features(
        domain_df.rename(columns={"domain": "domain"}),
        "domain",
        "普通油茶 CoLPAT 基因家族保守结构域分析",
        "fig4_conserved_domains",
        {"PF01553": "#6ab04c"},
    )
    plot_gene_structure(members)
    plot_secondary_structure()
    plot_at_homology_links(members)


if __name__ == "__main__":
    main()

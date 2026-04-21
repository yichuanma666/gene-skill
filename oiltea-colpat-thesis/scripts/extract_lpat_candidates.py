from __future__ import annotations

import gzip
import re
from collections import defaultdict
from pathlib import Path

import requests
from Bio.Align import PairwiseAligner, substitution_matrices
from Bio.Seq import Seq
from pyhmmer import easel, hmmer, plan7


ROOT = Path(r"F:\jyfx")
OUT = ROOT / "analysis_outputs"
GENOME = ROOT / "Camellia_oleifera_Changlin40.fasta"
GFF = ROOT / "Camellia_oleifera_Changlin40.gff3"
TAIR_CDS = ROOT / "TAIR.CDS.longest.fa"

PFAM_HMM_URL = "https://www.ebi.ac.uk/interpro/wwwapi/entry/pfam/PF01553?annotation=hmm"
PFAM_HMM = OUT / "PF01553.hmm"
ALL_PROTEINS = OUT / "Changlin40.predicted_proteins.fa"
ALL_CDS = OUT / "Changlin40.predicted_cds.fa"
META_TSV = OUT / "Changlin40.transcript_structure.tsv"
AT_LPAT_CDS = OUT / "Arabidopsis_LPAT_CDS.fa"
AT_LPAT_PROTEINS = OUT / "Arabidopsis_LPAT_proteins.fa"
HMM_TSV = OUT / "PF01553_hmm_hits.tsv"
CANDIDATE_TSV = OUT / "CoLPAT_candidates.tsv"
CANDIDATE_PROTEINS = OUT / "CoLPAT_candidates.proteins.fa"
CANDIDATE_CDS = OUT / "CoLPAT_candidates.cds.fa"

# Arabidopsis LPAT locus IDs used as homology anchors.
AT_LPAT_IDS = {
    "AT4G30580": "AtLPAT1",
    "AT3G57650": "AtLPAT2",
    "AT1G51260": "AtLPAT3",
    "AT1G75020": "AtLPAT4",
    "AT3G18850": "AtLPAT5",
}


def parse_attrs(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in text.strip().split(";"):
        if not item:
            continue
        if "=" in item:
            k, v = item.split("=", 1)
            out[k] = v
    return out


def chrom_key(chrom: str) -> tuple[int, str]:
    m = re.match(r"Chr(\d+)([a-z]*)$", chrom)
    if not m:
        return (10_000, chrom)
    return (int(m.group(1)), m.group(2))


def fasta_records(path: Path):
    name = None
    chunks: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    yield name, "".join(chunks)
                name = line[1:].split()[0]
                chunks = []
            else:
                chunks.append(line)
        if name is not None:
            yield name, "".join(chunks)


def write_fasta(handle, name: str, seq: str, width: int = 60):
    handle.write(f">{name}\n")
    for i in range(0, len(seq), width):
        handle.write(seq[i : i + width] + "\n")


def download_hmm():
    OUT.mkdir(exist_ok=True)
    if PFAM_HMM.exists() and PFAM_HMM.stat().st_size > 0:
        return
    response = requests.get(PFAM_HMM_URL, timeout=60)
    response.raise_for_status()
    data = gzip.decompress(response.content)
    PFAM_HMM.write_bytes(data)


def extract_at_lpat_queries() -> dict[str, dict[str, str]]:
    wanted = set(AT_LPAT_IDS)
    found: dict[str, dict[str, str]] = {}
    with TAIR_CDS.open("r", encoding="utf-8", errors="replace") as handle:
        header = None
        chunks: list[str] = []
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header:
                    locus = header[1:].split(".")[0].upper()
                    if locus in wanted:
                        cds = "".join(chunks).upper()
                        protein = str(Seq(cds).translate(to_stop=False)).rstrip("*")
                        found[locus] = {
                            "name": AT_LPAT_IDS[locus],
                            "header": header[1:],
                            "cds": cds,
                            "protein": protein,
                        }
                header = line
                chunks = []
            else:
                chunks.append(line)
        if header:
            locus = header[1:].split(".")[0].upper()
            if locus in wanted:
                cds = "".join(chunks).upper()
                protein = str(Seq(cds).translate(to_stop=False)).rstrip("*")
                found[locus] = {
                    "name": AT_LPAT_IDS[locus],
                    "header": header[1:],
                    "cds": cds,
                    "protein": protein,
                }
    if set(found) != wanted:
        missing = ", ".join(sorted(wanted - set(found)))
        raise RuntimeError(f"Missing Arabidopsis LPAT CDS: {missing}")

    with AT_LPAT_CDS.open("w", encoding="utf-8") as cds_out, AT_LPAT_PROTEINS.open(
        "w", encoding="utf-8"
    ) as pep_out:
        for locus in sorted(found):
            name = f"{found[locus]['name']}|{locus}|{found[locus]['header']}"
            write_fasta(cds_out, name, found[locus]["cds"])
            write_fasta(pep_out, name, found[locus]["protein"])
    return found


def load_gff_models():
    genes: dict[str, dict] = {}
    transcripts: dict[str, dict] = {}
    cds_by_tx: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    exons_by_tx: dict[str, list[tuple[int, int]]] = defaultdict(list)

    with GFF.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 9:
                continue
            seqid, source, feature, start, end, score, strand, phase, attrs = parts
            start_i, end_i = int(start), int(end)
            attr = parse_attrs(attrs)
            if feature == "gene":
                gid = attr.get("ID")
                if gid:
                    genes[gid] = {
                        "gene_id": gid,
                        "chrom": seqid,
                        "start": start_i,
                        "end": end_i,
                        "strand": strand,
                    }
            elif feature == "mRNA":
                tid = attr.get("ID")
                parent = attr.get("Parent")
                if tid and parent:
                    transcripts[tid] = {
                        "transcript_id": tid,
                        "gene_id": parent,
                        "chrom": seqid,
                        "start": start_i,
                        "end": end_i,
                        "strand": strand,
                    }
            elif feature == "CDS":
                parent = attr.get("Parent")
                if parent:
                    phase_i = 0 if phase == "." else int(phase)
                    cds_by_tx[parent].append((start_i, end_i, phase_i))
            elif feature == "exon":
                parent = attr.get("Parent")
                if parent:
                    exons_by_tx[parent].append((start_i, end_i))

    by_chrom: dict[str, list[str]] = defaultdict(list)
    for tid, rec in transcripts.items():
        if tid in cds_by_tx:
            by_chrom[rec["chrom"]].append(tid)
    for tids in by_chrom.values():
        tids.sort(key=lambda tid: (transcripts[tid]["start"], transcripts[tid]["end"], tid))
    return genes, transcripts, cds_by_tx, exons_by_tx, by_chrom


def extract_translated_models():
    if ALL_PROTEINS.exists() and META_TSV.exists() and ALL_CDS.exists():
        return

    genes, transcripts, cds_by_tx, exons_by_tx, by_chrom = load_gff_models()
    proteins_written = 0
    with ALL_PROTEINS.open("w", encoding="utf-8") as pep_out, ALL_CDS.open(
        "w", encoding="utf-8"
    ) as cds_out, META_TSV.open("w", encoding="utf-8") as meta:
        meta.write(
            "transcript_id\tgene_id\tchrom\tstart\tend\tstrand\tgene_length\t"
            "exon_count\tcds_count\tintron_count\tcds_length\taa_length\tinternal_stop\n"
        )
        for chrom, seq in fasta_records(GENOME):
            tids = by_chrom.get(chrom, [])
            if not tids:
                continue
            for tid in tids:
                rec = transcripts[tid]
                cds_parts = []
                for start, end, phase in sorted(cds_by_tx[tid], key=lambda x: x[0]):
                    cds_parts.append(seq[start - 1 : end])
                cds = "".join(cds_parts).upper()
                if rec["strand"] == "-":
                    cds = str(Seq(cds).reverse_complement())
                trim = len(cds) % 3
                cds_for_translation = cds[:-trim] if trim else cds
                protein = str(Seq(cds_for_translation).translate(to_stop=False))
                internal_stop = "*" in protein.rstrip("*")
                protein = protein.rstrip("*")
                if not protein:
                    continue
                write_fasta(
                    pep_out,
                    f"{tid}|gene={rec['gene_id']}|chrom={rec['chrom']}|start={rec['start']}|end={rec['end']}|strand={rec['strand']}",
                    protein,
                )
                write_fasta(cds_out, tid, cds)
                exon_count = len(exons_by_tx.get(tid, []))
                cds_count = len(cds_by_tx.get(tid, []))
                intron_count = max(0, exon_count - 1)
                meta.write(
                    f"{tid}\t{rec['gene_id']}\t{rec['chrom']}\t{rec['start']}\t{rec['end']}\t"
                    f"{rec['strand']}\t{rec['end'] - rec['start'] + 1}\t{exon_count}\t"
                    f"{cds_count}\t{intron_count}\t{len(cds)}\t{len(protein)}\t{internal_stop}\n"
                )
                proteins_written += 1
            print(f"processed {chrom}: {len(tids)} transcripts")
    print(f"translated proteins: {proteins_written}")


def run_hmmsearch():
    if HMM_TSV.exists() and HMM_TSV.stat().st_size > 100:
        return
    with plan7.HMMFile(PFAM_HMM) as hmm_file:
        hmm_model = next(hmm_file)
    with easel.SequenceFile(ALL_PROTEINS, digital=True, alphabet=hmm_model.alphabet) as seq_file:
        proteins = list(seq_file)
    hits = next(hmmer.hmmsearch(hmm_model, proteins, cpus=4, E=1e-5, domE=1e-5))
    with HMM_TSV.open("w", encoding="utf-8") as out:
        out.write(
            "target\taccession\tevalue\tscore\tbias\tdomains\tbest_domain_evalue\tbest_domain_score\n"
        )
        for hit in hits:
            if not hit.included:
                continue
            domains = [d for d in hit.domains if d.included]
            best_e = min((d.i_evalue for d in domains), default=hit.evalue)
            best_s = max((d.score for d in domains), default=0.0)
            hit_name = hit.name.decode() if isinstance(hit.name, bytes) else str(hit.name)
            hit_accession = ""
            if hit.accession:
                hit_accession = (
                    hit.accession.decode()
                    if isinstance(hit.accession, bytes)
                    else str(hit.accession)
                )
            out.write(
                f"{hit_name}\t{hit_accession}\t"
                f"{hit.evalue:.3g}\t{hit.score:.2f}\t{hit.bias:.2f}\t{len(domains)}\t"
                f"{best_e:.3g}\t{best_s:.2f}\n"
            )


def load_fasta_dict(path: Path) -> dict[str, str]:
    return {name: seq for name, seq in fasta_records(path)}


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        return [dict(zip(header, line.rstrip("\n").split("\t"))) for line in handle if line.strip()]


def protein_name_to_tid(name: str) -> str:
    return name.split("|", 1)[0]


def build_candidates(at_queries: dict[str, dict[str, str]]):
    proteins = load_fasta_dict(ALL_PROTEINS)
    cds = load_fasta_dict(ALL_CDS)
    meta = {row["transcript_id"]: row for row in load_tsv(META_TSV)}
    hmm_hits = load_tsv(HMM_TSV)

    aligner = PairwiseAligner()
    aligner.mode = "local"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -10
    aligner.extend_gap_score = -0.5

    rows = []
    for hit in hmm_hits:
        tid = protein_name_to_tid(hit["target"])
        protein = proteins[hit["target"]]
        best = None
        for locus, q in at_queries.items():
            score = aligner.score(q["protein"], protein)
            norm = score / max(1, min(len(q["protein"]), len(protein)))
            item = (norm, score, q["name"], locus)
            if best is None or item > best:
                best = item
        assert best is not None
        norm, score, at_name, at_locus = best
        m = meta[tid]
        rows.append(
            {
                **m,
                "target_name": hit["target"],
                "hmm_evalue": hit["evalue"],
                "hmm_score": hit["score"],
                "best_domain_evalue": hit["best_domain_evalue"],
                "best_domain_score": hit["best_domain_score"],
                "best_at_lpat": at_name,
                "best_at_locus": at_locus,
                "at_similarity_score": f"{score:.2f}",
                "at_similarity_norm": f"{norm:.3f}",
                "protein_seq": protein,
                "cds_seq": cds.get(tid, ""),
            }
        )

    rows.sort(
        key=lambda r: (
            chrom_key(r["chrom"]),
            int(r["start"]),
            int(r["end"]),
            r["transcript_id"],
        )
    )
    for i, row in enumerate(rows, 1):
        row["colpat_name"] = f"CoLPAT{i}"

    cols = [
        "colpat_name",
        "gene_id",
        "transcript_id",
        "chrom",
        "start",
        "end",
        "strand",
        "gene_length",
        "exon_count",
        "intron_count",
        "cds_length",
        "aa_length",
        "hmm_evalue",
        "hmm_score",
        "best_domain_evalue",
        "best_domain_score",
        "best_at_lpat",
        "best_at_locus",
        "at_similarity_score",
        "at_similarity_norm",
        "internal_stop",
    ]
    with CANDIDATE_TSV.open("w", encoding="utf-8") as out:
        out.write("\t".join(cols) + "\n")
        for row in rows:
            out.write("\t".join(str(row[c]) for c in cols) + "\n")
    with CANDIDATE_PROTEINS.open("w", encoding="utf-8") as pep_out, CANDIDATE_CDS.open(
        "w", encoding="utf-8"
    ) as cds_out:
        for row in rows:
            header = (
                f"{row['colpat_name']}|{row['transcript_id']}|{row['chrom']}:{row['start']}-{row['end']}"
                f"({row['strand']})|best={row['best_at_lpat']}|hmm_e={row['hmm_evalue']}"
            )
            write_fasta(pep_out, header, row["protein_seq"])
            write_fasta(cds_out, header, row["cds_seq"])
    print(f"PF01553 candidate count: {len(rows)}")


def main():
    OUT.mkdir(exist_ok=True)
    download_hmm()
    at_queries = extract_at_lpat_queries()
    extract_translated_models()
    run_hmmsearch()
    build_candidates(at_queries)


if __name__ == "__main__":
    main()

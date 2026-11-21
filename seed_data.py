"""
seed_data.py — Initial protein data seeder for EndolysinDB.

Parses data/sequences/initial_proteins.fasta using Biopython.
Idempotent: safe to run multiple times; never creates duplicate records.
No biological data is fabricated. Missing fields are left NULL.

Usage:
    python seed_data.py
"""

import os
import sys

# Ensure project root is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Bio import SeqIO

from app import create_app
from models import db, Protein, Structure

# ---------------------------------------------------------------------------
# FASTA file location
# ---------------------------------------------------------------------------
FASTA_PATH = os.path.join("data", "sequences", "initial_proteins.fasta")

# ---------------------------------------------------------------------------
# Project display names for each accession.
# FASTA name (fasta_name) is preserved exactly as parsed from the header.
# Display name (name) is the project identifier used in the application.
# Art-35 retains both identifiers as requested.
# ---------------------------------------------------------------------------
DISPLAY_NAMES = {
    "Q6Y7T6": "LysK",
    "D6QY02": "LysGH15",
    "P15057": "CP1",
    "Q7Y3F1": "PlyC",
    "Q8SD18": "Art-35",
}

# ---------------------------------------------------------------------------
# Structure and annotation image mappings.
# Paths are relative to the data/ directory, served via /data/<path:filename>.
# PDB IDs are NOT assigned here — only confirmed image files are recorded.
# Structure images and annotation images are stored in separate columns.
# ---------------------------------------------------------------------------
STRUCTURE_IMAGES = {
    "Q6Y7T6": {  # LysK
        "structure_image_path": "structures/LysK_structure.png",
        "annotation_image_path": "annotations/LysK_annotation.png",
        "source": "unknown (image provided)",
        "notes": (
            "Structure and annotation images provided. "
            "PDB ID not yet assigned — verify before linking."
        ),
    },
    "D6QY02": {  # LysGH15
        "structure_image_path": "structures/LysGH15_structure.png",
        "annotation_image_path": "annotations/LysGH15_annotation.png",
        "source": "unknown (image provided)",
        "notes": (
            "Structure and annotation images provided. "
            "PDB ID not yet assigned — verify before linking."
        ),
    },
    "P15057": {  # CP1
        "structure_image_path": "structures/CP1_structure.png",
        "annotation_image_path": "annotations/CP1_annotation.png",
        "source": "unknown (image provided)",
        "notes": (
            "Structure and annotation images provided. "
            "PDB ID not yet assigned — verify before linking."
        ),
    },
    "Q7Y3F1": {  # PlyC
        # PlyC structure image is located in the annotations directory
        "structure_image_path": "annotations/PlyC_structure.png",
        "annotation_image_path": "annotations/PlyC_annotation.png",
        "source": "unknown (image provided)",
        "notes": (
            "Structure image is located in annotations/ directory. "
            "PDB ID not yet assigned — verify before linking."
        ),
    },
    "Q8SD18": {  # Art-35 / gp144
        # Art-35 structure image is located in the annotations directory
        "structure_image_path": "annotations/Art35_structure.png",
        "annotation_image_path": "annotations/Art35_annotation.png",
        "source": "unknown (image provided)",
        "notes": (
            "Known in FASTA as gp144 (gene PHIKZ144). Project name: Art-35. "
            "Structure image in annotations/ directory. "
            "PDB ID not yet assigned — verify before linking."
        ),
    },
}


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_uniprot_header(header: str) -> dict:
    """
    Parse a UniProt Swiss-Prot FASTA header.

    Format:
        sp|ACCESSION|ENTRY_NAME Description OS=Organism OX=TaxID GN=Gene PE=N SV=N

    Returns a dict with keys:
        accession, entry_name, fasta_description, organism, gene_name
    """
    result = {}

    # First token is 'sp|ACCESSION|ENTRY_NAME'
    tokens = header.split()
    first = tokens[0]
    parts = first.split("|")
    if len(parts) >= 3:
        result["accession"] = parts[1]
        result["entry_name"] = parts[2]
    elif len(parts) == 2:
        result["accession"] = parts[1]
        result["entry_name"] = None
    else:
        result["accession"] = None
        result["entry_name"] = None

    # Everything after the first token
    rest = header[len(first):].strip()

    # Description = text before OS=
    if "OS=" in rest:
        idx = rest.index("OS=")
        result["fasta_description"] = rest[:idx].strip()
        os_and_beyond = rest[idx + 3:]
        # Organism ends at next field marker
        for stop in (" OX=", " GN=", " PE=", " SV="):
            if stop in os_and_beyond:
                os_and_beyond = os_and_beyond[: os_and_beyond.index(stop)]
        result["organism"] = os_and_beyond.strip()
    else:
        result["fasta_description"] = rest.strip()
        result["organism"] = None

    # Gene name from GN=
    if "GN=" in rest:
        gn_start = rest.index("GN=") + 3
        gn_val = rest[gn_start:]
        for stop in (" OX=", " OS=", " PE=", " SV="):
            if stop in gn_val:
                gn_val = gn_val[: gn_val.index(stop)]
        result["gene_name"] = gn_val.strip()
    else:
        result["gene_name"] = None

    return result


def extract_fasta_name(parsed: dict) -> str:
    """
    Extract the name as it appears in the FASTA description.
    For UniProt headers the description token starts with the protein name.
    e.g. 'Endolysin LysK' → 'LysK', 'Endolysin gp144' → 'gp144',
    'Lysozyme' → 'Lysozyme'
    """
    desc = parsed.get("fasta_description", "") or ""
    # Try to find the second word if description starts with 'Endolysin' or 'Lysozyme'
    words = desc.split()
    if len(words) >= 2 and words[0].lower() in ("endolysin", "lysozyme"):
        return words[1].rstrip(",")
    elif words:
        return words[0]
    return desc


# ---------------------------------------------------------------------------
# Seeder
# ---------------------------------------------------------------------------

def seed_proteins(verbose: bool = True) -> None:
    """
    Parse FASTA and insert protein + structure records.
    Checks for existing accession before inserting (idempotent).
    """
    if not os.path.exists(FASTA_PATH):
        print(f"[ERROR] FASTA file not found: {FASTA_PATH}")
        return

    inserted = 0
    skipped = 0

    for record in SeqIO.parse(FASTA_PATH, "fasta"):
        # record.description is the full header line (without '>') as a string
        header = record.description
        parsed = parse_uniprot_header(header)
        accession = parsed.get("accession")

        if not accession:
            print(f"[WARN]  Could not parse accession from header: {header[:80]}")
            continue

        # Idempotency check — skip if accession already in DB
        existing = Protein.query.filter_by(accession=accession).first()
        if existing:
            if verbose:
                print(f"[SKIP]  {accession} ({existing.name}) — already in database")
            skipped += 1
            continue

        sequence = str(record.seq)
        display_name = DISPLAY_NAMES.get(accession, parsed.get("fasta_description", accession))
        fasta_name = extract_fasta_name(parsed)
        organism = parsed.get("organism")

        protein = Protein(
            accession=accession,
            name=display_name,
            fasta_name=fasta_name,
            fasta_header=header,          # full original header preserved verbatim
            sequence=sequence,
            length=len(sequence),
            organism=organism,
            phage=organism,               # phage is the host organism string from OS= field
            description=parsed.get("fasta_description"),
        )
        db.session.add(protein)
        # Flush to obtain protein.id before creating the linked structure record
        db.session.flush()

        # Insert structure record using only confirmed image files
        struct_data = STRUCTURE_IMAGES.get(accession)
        if struct_data:
            structure = Structure(
                protein_id=protein.id,
                pdb_id=None,                            # not assigned — set manually from PDB
                structure_image_path=struct_data["structure_image_path"],
                annotation_image_path=struct_data["annotation_image_path"],
                coordinate_file_path=None,              # no .pdb/.cif file present yet
                source=struct_data["source"],
                notes=struct_data["notes"],
            )
            db.session.add(structure)

        if verbose:
            print(
                f"[INSERT] {accession} | name={display_name!r} | "
                f"fasta_name={fasta_name!r} | length={len(sequence)} aa"
            )
        inserted += 1

    db.session.commit()
    print(f"\n[DONE] Inserted: {inserted}  Skipped (already exist): {skipped}")


def main():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("EndolysinDB — Seed Data")
        print("=" * 60)
        seed_proteins(verbose=True)


if __name__ == "__main__":
    main()

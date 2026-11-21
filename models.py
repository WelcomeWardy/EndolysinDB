"""
models.py — SQLAlchemy ORM models for EndolysinDB.

Six normalized tables:
  proteins          — core protein records with accession UNIQUE constraint
  domains           — domain annotations (SVG only rendered when start/end coords present)
  target_organisms  — host range records with evidence_type (not a boolean)
  activities        — experimental conditions with evidence_type
  engineering       — engineered variants and chimeras
  structures        — image paths and PDB IDs kept strictly separate

No biological data is fabricated here. Missing fields remain NULL.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate_ext = Migrate()


class Protein(db.Model):
    __tablename__ = "proteins"

    id = db.Column(db.Integer, primary_key=True)

    # UniProt or NCBI accession — must be unique, never NULL
    accession = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Project display name (e.g. "Art-35") — may differ from FASTA name
    name = db.Column(db.String(100), nullable=False)

    # Name exactly as it appears in the FASTA header (e.g. "gp144" for Art-35)
    fasta_name = db.Column(db.String(100))

    # Complete original FASTA header line, preserved verbatim
    fasta_header = db.Column(db.Text)

    # Full amino acid sequence
    sequence = db.Column(db.Text, nullable=False)

    # Computed from sequence on insert
    length = db.Column(db.Integer)

    # Host organism of the phage (from FASTA OS= field)
    organism = db.Column(db.String(200))

    # Phage name (from FASTA OS= field — same field, more specific)
    phage = db.Column(db.String(200))

    # Functional description from FASTA header
    description = db.Column(db.Text)

    # Self-referential FK: set for engineered/chimeric proteins derived from a parent
    parent_protein_id = db.Column(
        db.Integer, db.ForeignKey("proteins.id"), nullable=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    domains = db.relationship(
        "Domain", backref="protein", lazy=True, cascade="all, delete-orphan"
    )
    structures = db.relationship(
        "Structure", backref="protein", lazy=True, cascade="all, delete-orphan"
    )
    targets = db.relationship(
        "TargetOrganism", backref="protein", lazy=True, cascade="all, delete-orphan"
    )
    activities = db.relationship(
        "Activity", backref="protein", lazy=True, cascade="all, delete-orphan"
    )
    engineering_records = db.relationship(
        "Engineering",
        foreign_keys="Engineering.parent_protein_id",
        backref="parent_protein",
        lazy=True,
    )

    def __repr__(self):
        return f"<Protein {self.accession} | {self.name}>"


class Domain(db.Model):
    """
    Domain annotation record.
    start_pos and end_pos are populated only from real InterPro/InterProScan output.
    Domain SVG diagrams are rendered only when both coordinates are present.
    """

    __tablename__ = "domains"

    id = db.Column(db.Integer, primary_key=True)
    protein_id = db.Column(
        db.Integer, db.ForeignKey("proteins.id"), nullable=False, index=True
    )

    domain_name = db.Column(db.String(200), nullable=False)

    # Functional category: e.g. CHAP, Amidase_2, CBD, LysM, SH3b
    domain_type = db.Column(db.String(100))

    # Residue positions — NULL until verified InterProScan data is loaded
    start_pos = db.Column(db.Integer, nullable=True)
    end_pos = db.Column(db.Integer, nullable=True)

    description = db.Column(db.Text)

    # Data origin: 'InterPro', 'Pfam', 'CDD', 'manual'
    source = db.Column(db.String(100))

    # InterPro entry identifier if applicable
    interpro_id = db.Column(db.String(20))

    def __repr__(self):
        coords = f"[{self.start_pos}-{self.end_pos}]" if self.start_pos else "[no coords]"
        return f"<Domain {self.domain_name} {coords}>"


class TargetOrganism(db.Model):
    """
    Records of bacterial species/strains that a protein has been tested against.

    evidence_type distinguishes how the host range was determined:
      'experimental' — directly demonstrated in a published assay
      'literature'   — reported in a secondary source or review
      'inferred'     — inferred from phage host range, not directly tested
    """

    __tablename__ = "target_organisms"

    id = db.Column(db.Integer, primary_key=True)
    protein_id = db.Column(
        db.Integer, db.ForeignKey("proteins.id"), nullable=False, index=True
    )

    organism_name = db.Column(db.String(200), nullable=False)
    strain = db.Column(db.String(200), nullable=True)

    # Type of antibacterial effect observed
    activity_type = db.Column(db.String(100), nullable=True)  # e.g. 'lytic', 'bactericidal'

    # MIC or comparable metric — stored as text to allow "N/A", ">128 µg/mL", ranges
    mic_value = db.Column(db.String(100), nullable=True)

    assay_method = db.Column(db.String(200), nullable=True)

    # 'experimental' | 'literature' | 'inferred' — never a boolean
    evidence_type = db.Column(db.String(50), nullable=True)

    # DOI of the primary source supporting this record
    reference_doi = db.Column(db.String(500), nullable=True)

    # Free-text citation or note when DOI is unavailable
    reference_note = db.Column(db.Text, nullable=True)

    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<TargetOrganism {self.organism_name} ← protein {self.protein_id}>"


class Activity(db.Model):
    """
    Experimental conditions under which activity was measured.
    Records biochemical parameters, not host-range outcomes.
    """

    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    protein_id = db.Column(
        db.Integer, db.ForeignKey("proteins.id"), nullable=False, index=True
    )

    # e.g. 'muralytic', 'bactericidal', 'synergistic', 'turbidity reduction'
    activity_type = db.Column(db.String(100), nullable=True)

    # Assay conditions — all nullable (not all papers report all parameters)
    ph = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)        # °C
    salt_conc = db.Column(db.String(50), nullable=True)     # e.g. "150 mM NaCl"

    assay_method = db.Column(db.String(200), nullable=True)

    # 'experimental' | 'literature'
    evidence_type = db.Column(db.String(50), nullable=True)

    reference_doi = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Activity {self.activity_type} | protein {self.protein_id}>"


class Engineering(db.Model):
    """
    Records of engineered variants, truncations, fusions, and chimeras
    derived from a parent endolysin.
    """

    __tablename__ = "engineering"

    id = db.Column(db.Integer, primary_key=True)
    parent_protein_id = db.Column(
        db.Integer, db.ForeignKey("proteins.id"), nullable=False, index=True
    )

    engineered_name = db.Column(db.String(200), nullable=False)

    # Description of mutations introduced (point mutations, truncations)
    mutation_info = db.Column(db.Text, nullable=True)

    # For chimeras: which domains were taken from which sources
    chimera_composition = db.Column(db.Text, nullable=True)

    original_host_range = db.Column(db.Text, nullable=True)
    modified_host_range = db.Column(db.Text, nullable=True)

    reference_doi = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Engineering {self.engineered_name} ← {self.parent_protein_id}>"


class Structure(db.Model):
    """
    Structure and annotation image records.
    PDB identifiers, image file paths, and coordinate files are kept
    in separate columns and are never conflated.
    """

    __tablename__ = "structures"

    id = db.Column(db.Integer, primary_key=True)
    protein_id = db.Column(
        db.Integer, db.ForeignKey("proteins.id"), nullable=False, index=True
    )

    # 4-character PDB accession — NULL until a confirmed PDB entry is linked
    pdb_id = db.Column(db.String(10), nullable=True)

    # Path to rendered structure image (relative to data/ dir), served via /data/ route
    structure_image_path = db.Column(db.String(500), nullable=True)

    # Path to domain annotation image (from InterPro/manual), separate from structure image
    annotation_image_path = db.Column(db.String(500), nullable=True)

    # Path to coordinate file (.pdb or .cif) — NULL until file is present
    coordinate_file_path = db.Column(db.String(500), nullable=True)

    # 'PDB', 'AlphaFold', 'manual', 'unknown'
    source = db.Column(db.String(100), nullable=True)

    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        pdb = self.pdb_id or "no PDB"
        return f"<Structure {pdb} | protein {self.protein_id}>"

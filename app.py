"""
app.py — Flask application factory for EndolysinDB.

All routes live here for Phase 1. No blueprints — flat structure as agreed.
"""

import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from sqlalchemy import text, or_

from config import Config
from models import db, migrate_ext


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate_ext.init_app(app, db)

    # Register models so Flask-Migrate can detect them
    from models import Protein, Domain, TargetOrganism, Activity, Engineering, Structure

    # -------------------------------------------------------------------------
    # Data-serving route — serves files from the data/ directory
    # (structure images, annotation images)
    # -------------------------------------------------------------------------

    @app.route("/data/<path:filename>")
    def serve_data(filename):
        data_dir = os.path.join(app.root_path, "data")
        return send_from_directory(data_dir, filename)

    # -------------------------------------------------------------------------
    # Main routes
    # -------------------------------------------------------------------------

    @app.route("/")
    def index():
        proteins = Protein.query.order_by(Protein.name).all()
        stats = {
            "proteins": Protein.query.count(),
            "domains": Domain.query.count(),
            "targets": TargetOrganism.query.count(),
            "activities": Activity.query.count(),
        }
        return render_template("index.html", proteins=proteins, stats=stats)

    @app.route("/proteins")
    def proteins():
        all_proteins = Protein.query.order_by(Protein.name).all()
        return render_template("proteins.html", proteins=all_proteins)

    @app.route("/proteins/<int:protein_id>")
    def protein_detail(protein_id):
        # Flask-SQLAlchemy 3.x / SQLAlchemy 2.x safe lookup
        protein = db.get_or_404(Protein, protein_id)

        domains = Domain.query.filter_by(protein_id=protein_id).all()

        # Only signal SVG rendering when genuine coordinate data is present
        has_domain_coords = any(
            d.start_pos is not None and d.end_pos is not None for d in domains
        )

        targets = TargetOrganism.query.filter_by(protein_id=protein_id).all()
        activities = Activity.query.filter_by(protein_id=protein_id).all()
        structures = Structure.query.filter_by(protein_id=protein_id).all()
        engineering = Engineering.query.filter_by(
            parent_protein_id=protein_id
        ).all()

        # Extract image paths from structure record (kept separate)
        annotation_image = None
        structure_image = None
        for s in structures:
            if s.annotation_image_path and annotation_image is None:
                annotation_image = s.annotation_image_path
            if s.structure_image_path and structure_image is None:
                structure_image = s.structure_image_path

        return render_template(
            "protein_detail.html",
            protein=protein,
            domains=domains,
            has_domain_coords=has_domain_coords,
            targets=targets,
            activities=activities,
            structures=structures,
            engineering=engineering,
            annotation_image=annotation_image,
            structure_image=structure_image,
        )

    @app.route("/search")
    def search():
        q = request.args.get("q", "").strip()
        results = []
        searched = False

        if q:
            searched = True
            like = f"%{q}%"

            # Search proteins by name, accession, organism, phage, description
            protein_hits = Protein.query.filter(
                or_(
                    Protein.name.ilike(like),
                    Protein.accession.ilike(like),
                    Protein.organism.ilike(like),
                    Protein.phage.ilike(like),
                    Protein.description.ilike(like),
                )
            ).all()

            # Also search by target organism name/strain
            target_hits = TargetOrganism.query.filter(
                or_(
                    TargetOrganism.organism_name.ilike(like),
                    TargetOrganism.strain.ilike(like),
                )
            ).all()

            # Collect proteins from target hits, deduplicating
            seen_ids = {p.id for p in protein_hits}
            for t in target_hits:
                if t.protein_id not in seen_ids:
                    p = db.session.get(Protein, t.protein_id)
                    if p:
                        protein_hits.append(p)
                        seen_ids.add(p.id)

            results = protein_hits

        return render_template(
            "search.html", query=q, results=results, searched=searched
        )

    # -------------------------------------------------------------------------
    # Health check and API
    # -------------------------------------------------------------------------

    @app.route("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            db_status = "connected"
            status = "healthy"
        except Exception as exc:
            db_status = f"error: {exc}"
            status = "degraded"

        return jsonify({"status": status, "database": db_status})

    @app.route("/api/stats")
    def api_stats():
        return jsonify(
            {
                "proteins": Protein.query.count(),
                "domains": Domain.query.count(),
                "target_organisms": TargetOrganism.query.count(),
                "activities": Activity.query.count(),
                "engineering": Engineering.query.count(),
                "structures": Structure.query.count(),
            }
        )

    # -------------------------------------------------------------------------
    # Error handlers
    # -------------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app

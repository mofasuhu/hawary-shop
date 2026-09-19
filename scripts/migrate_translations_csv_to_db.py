"""Migrate translations from CSV file to the database."""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.translation import Translation


def migrate_csv_to_db(csv_file=None):
    if csv_file is None:
        csv_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db - translation.csv")

    with open(csv_file, "r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            key = row["key"]
            value_en = row["value_en"]
            value_ar = row["value_ar"]
            existing = db.session.query(Translation).filter_by(key=key).first()
            if not existing:
                db.session.add(Translation(key=key, value_en=value_en, value_ar=value_ar))
                print(f"Added new translation for key: {key}")
            else:
                updated = False
                if existing.value_en != value_en:
                    existing.value_en = value_en; updated = True
                if existing.value_ar != value_ar:
                    existing.value_ar = value_ar; updated = True
                if updated:
                    print(f"Updated translation for key: {key}")
                else:
                    print(f"No changes needed for key: {key}")
    db.session.commit()
    print("Data successfully migrated from CSV to the database.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        migrate_csv_to_db()

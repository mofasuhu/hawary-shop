"""Populate/update governorate delivery fees in the database."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.delivery import GovernorateDeliveryFee
from app.config import EGYPT_GOVERNORATES


def populate_governorate_delivery_fees():
    default_base_fee = 70.0
    default_per_kg_rate = 7.0

    governorate_rates = {
        "cairo": {"base_fee": 10.0, "per_kg_rate": 5.0, "is_covered": True},
        "giza": {"base_fee": 60.0, "per_kg_rate": 5.5, "is_covered": True},
        "new_cairo": {"base_fee": 55.0, "per_kg_rate": 5.0, "is_covered": True},
        "6th_of_october": {"base_fee": 65.0, "per_kg_rate": 5.75, "is_covered": True},
        "sheikh_zayed": {"base_fee": 65.0, "per_kg_rate": 5.75, "is_covered": True},
        "obour": {"base_fee": 55.0, "per_kg_rate": 5.5, "is_covered": True},
        "shorouk": {"base_fee": 60.0, "per_kg_rate": 5.5, "is_covered": True},
        "badr": {"base_fee": 60.0, "per_kg_rate": 5.5, "is_covered": True},
        "hadayek_october": {"base_fee": 65.0, "per_kg_rate": 5.75, "is_covered": True},
        "hadayek_el_ahram": {"base_fee": 65.0, "per_kg_rate": 5.75, "is_covered": True},
        "new_administrative_capital": {"base_fee": 65.0, "per_kg_rate": 5.75, "is_covered": True},
        "10th_of_ramadan": {"base_fee": 65.0, "per_kg_rate": 5.75, "is_covered": True},
        "helwan": {"base_fee": 65.0, "per_kg_rate": 5.75, "is_covered": True},
        "alexandria": {"base_fee": 100.0, "per_kg_rate": 6.0, "is_covered": True},
        "new_alamein": {"base_fee": 200.0, "per_kg_rate": 7.5, "is_covered": True},
        "dakahlia": {"base_fee": 100.0, "per_kg_rate": 6.5, "is_covered": True},
        "red_sea": {"base_fee": 200.0, "per_kg_rate": 10.0, "is_covered": True},
        "beheira": {"base_fee": 100.0, "per_kg_rate": 6.5, "is_covered": True},
        "fayoum": {"base_fee": 100.0, "per_kg_rate": 7.0, "is_covered": True},
        "gharbia": {"base_fee": 100.0, "per_kg_rate": 6.5, "is_covered": True},
        "ismailia": {"base_fee": 100.0, "per_kg_rate": 7.0, "is_covered": True},
        "menofia": {"base_fee": 100.0, "per_kg_rate": 6.5, "is_covered": True},
        "minya": {"base_fee": 100.0, "per_kg_rate": 8.0, "is_covered": True},
        "qalyubia": {"base_fee": 70.0, "per_kg_rate": 5.5, "is_covered": True},
        "new_valley": {"base_fee": 200.0, "per_kg_rate": 12.0, "is_covered": True},
        "suez": {"base_fee": 100.0, "per_kg_rate": 7.5, "is_covered": True},
        "asyut": {"base_fee": 150.0, "per_kg_rate": 8.5, "is_covered": True},
        "qena": {"base_fee": 170.0, "per_kg_rate": 9.0, "is_covered": True},
        "damietta": {"base_fee": 130.0, "per_kg_rate": 7.0, "is_covered": True},
        "sohag": {"base_fee": 180.0, "per_kg_rate": 9.0, "is_covered": True},
        "north_sinai": {"base_fee": 200.0, "per_kg_rate": 11.0, "is_covered": False},
        "south_sinai": {"base_fee": 200.0, "per_kg_rate": 11.0, "is_covered": False},
        "kafr_el_sheikh": {"base_fee": 100.0, "per_kg_rate": 7.0, "is_covered": True},
        "matrouh": {"base_fee": 200.0, "per_kg_rate": 10.0, "is_covered": True},
        "luxor": {"base_fee": 200.0, "per_kg_rate": 9.5, "is_covered": True},
        "beni_suef": {"base_fee": 100.0, "per_kg_rate": 7.5, "is_covered": True},
        "port_said": {"base_fee": 110.0, "per_kg_rate": 7.5, "is_covered": True},
        "sharqia": {"base_fee": 100.0, "per_kg_rate": 6.0, "is_covered": True},
        "aswan": {"base_fee": 200.0, "per_kg_rate": 10.5, "is_covered": True},
    }

    try:
        for gov_name in EGYPT_GOVERNORATES:
            rates = governorate_rates.get(gov_name, {
                "base_fee": default_base_fee, "per_kg_rate": default_per_kg_rate, "is_covered": False
            })
            existing = GovernorateDeliveryFee.query.filter_by(governorate_name=gov_name).first()
            if existing:
                print(f"Updating entry for {gov_name}...")
                existing.base_fee = rates["base_fee"]
                existing.per_kg_rate = rates["per_kg_rate"]
                existing.is_covered = rates["is_covered"]
            else:
                print(f"Adding new entry for {gov_name}...")
                db.session.add(GovernorateDeliveryFee(
                    governorate_name=gov_name, base_fee=rates["base_fee"],
                    per_kg_rate=rates["per_kg_rate"], is_covered=rates["is_covered"]
                ))
        db.session.commit()
        print("Governorate delivery fees populated/updated successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        populate_governorate_delivery_fees()

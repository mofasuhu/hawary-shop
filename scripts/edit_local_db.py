import importlib.util
from dotenv import load_dotenv

# --- IMPORTANT: Ensure this script uses the LOCAL database credentials ---
# It's assumed your .env file is currently pointing to your local DB for this step.
load_dotenv()

# --- Boilerplate to load your Flask app and database models ---
module_path = "app.py"
module_name = "app"
spec = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Access your app and db objects
app = module.app
db = module.db

# Import your models after the app is loaded
User = module.User
Order = module.Order
Product = module.Product
# ... import any other models you need to edit ...

# --- The Main Editing Function ---
def perform_edits():
    """
    Connects to the database and performs specific, programmatic edits.
    """
    print("Connecting to the database to perform edits...")

    # --- EXAMPLE 1: Change the price of a specific product ---
    product_to_edit = db.session.query(Product).filter_by(id=15).first()
    if product_to_edit:
        print("Found product with ID 15. Changing its name.")
        product_to_edit.name_en = "New Updated Product Name"
        product_to_edit.name_ar = "اسم المنتج الجديد المحدث"
    
    # --- EXAMPLE 2: Give a specific user admin rights ---
    user_to_promote = db.session.query(User).filter_by(email='someuser@example.com').first()
    if user_to_promote:
        print(f"Promoting user {user_to_promote.email} to admin.")
        user_to_promote.role = 'admin'

    # --- EXAMPLE 3: Correct a typo in all order statuses ---
    orders_to_fix = db.session.query(Order).filter_by(status="Pendng").all() # Note the typo
    if orders_to_fix:
        print(f"Found {len(orders_to_fix)} orders with typo in status. Correcting them.")
        for order in orders_to_fix:
            order.status = "Pending"

    # After making all your changes, commit them to the database.
    try:
        db.session.commit()
        print("\nSUCCESS: All edits have been committed to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"\nERROR: An error occurred during commit. Rolling back changes. Error: {e}")


if __name__ == '__main__':
    # Run the editing script within the Flask app context
    with app.app_context():
        perform_edits()

# # example version that can remove All 'Delivered' or 'Cancelled' orders dated before the cutoff_date:
# import importlib.util
# from datetime import datetime
# from dateutil.relativedelta import relativedelta
# from zoneinfo import ZoneInfo
# from dotenv import load_dotenv

# # --- Load local environment (must point to local DB) ---
# load_dotenv()

# # --- Load your Flask app ---
# module_path = "app.py"
# module_name = "app"
# spec = importlib.util.spec_from_file_location(module_name, module_path)
# module = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(module)

# # Access app/db/models
# app = module.app
# db = module.db
# Order = module.Order
# Transaction = module.Transaction
# OrderItem = module.OrderItem

# # --- Utility for finding first day of last month/year ---
# def get_date_cutoff(period='month'):
#     now = datetime.now(ZoneInfo("Africa/Cairo"))
#     if period == 'month':
#         cutoff = now.replace(day=1) - relativedelta(months=1)
#     elif period == 'year':
#         cutoff = now.replace(month=1, day=1) - relativedelta(years=1)
#     else:
#         raise ValueError("Invalid period. Use 'month' or 'year'.")
#     return cutoff.replace(hour=0, minute=0, second=0, microsecond=0)

# # --- The Cleanup Logic ---
# def cleanup_old_orders(period='month'):
#     print(f"Starting cleanup for '{period}'...")

#     cutoff_date = get_date_cutoff(period)
#     print(f"Deleting Delivered/Cancelled orders before: {cutoff_date}")

#     old_orders = db.session.query(Order).filter(
#         Order.status.in_(['Delivered', 'Cancelled']),
#         Order.date < cutoff_date
#     ).all()

#     print(f"Found {len(old_orders)} orders to delete.")

#     deleted_transactions = 0
#     deleted_items = 0

#     for order in old_orders:
#         # Delete associated transaction
#         if order.transaction:
#             db.session.delete(order.transaction)
#             deleted_transactions += 1

#         # Delete all order items
#         for item in order.items:
#             db.session.delete(item)
#             deleted_items += 1

#         # Delete the order itself
#         db.session.delete(order)

#     try:
#         db.session.commit()
#         print("✅ Successfully deleted:")
#         print(f"   - Orders: {len(old_orders)}")
#         print(f"   - Transactions: {deleted_transactions}")
#         print(f"   - Order Items: {deleted_items}")
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ ERROR: {e}")
#         print("Changes rolled back.")

# # --- Entry Point ---
# if __name__ == '__main__':
#     with app.app_context():
#         cleanup_old_orders(period='month')  # You can also call 'year'



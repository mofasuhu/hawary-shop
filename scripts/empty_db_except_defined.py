import importlib.util
from sqlalchemy import MetaData

module_path = "app.py"
module_name = "app"

# comment out the tables that you want to empty 

SKIP_TABLES = [
    'alembic_version',
    'failed_transaction',
    'governorate_delivery_fee',
    'order',
    'order_item',
    'product',
    'product_size',
    'promo_code',
    'temp_order_data',
    'transaction',
    'translation',
    'user',
    'user_cart',
    # 'visitor_log',
    # 'webhook_debug_log'
]


SKIP_LIST_STR = '\n'.join(SKIP_TABLES)

spec = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Access `db` and `app` from the loaded module
db = module.db
app = module.app

def empty_all_except_user_and_alembic():
    # Get the metadata
    metadata = MetaData()
    engine = db.engine  # Use the engine directly
    metadata.reflect(bind=engine)

    # Get tables in an order that respects foreign key dependencies for deletion.
    # metadata.sorted_tables gives tables in creation order (dependencies first).
    # We need the reverse order for deletion (dependents first)
    tables_to_delete = list(reversed(metadata.sorted_tables))

    with engine.begin() as connection:
        for table in tables_to_delete:
            if table.name not in SKIP_TABLES:
                print(f"Deleting all rows from {table.name}...")
                connection.execute(table.delete())
    
    print(f"All tables except:\n{SKIP_LIST_STR}\nhave been emptied.")

if __name__ == '__main__':
    sure = input(f"Are you sure you want to empty all tables except:\n{SKIP_LIST_STR}\nfrom db? type yes or no\nYour Input: ")
    if sure.strip().lower() == "yes":
        # Run the database operations inside the Flask app context
        with app.app_context():
            empty_all_except_user_and_alembic()
    else:
        print("Thanks!")

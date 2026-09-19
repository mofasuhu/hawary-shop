import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', '5432')

def restore_from_backup(backup_file_path):
    if not os.path.exists(backup_file_path):
        print(f"Error: Backup file not found at '{backup_file_path}'")
        return

    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print("Error: Database credentials are not fully configured in .env file.")
        return

    print("-" * 50)
    print("!!! WARNING: THIS IS A DESTRUCTIVE OPERATION !!!")
    print(f"You are about to WIPE the database '{DB_NAME}' on host '{DB_HOST}'")
    print(f"and restore it from the file '{backup_file_path}'.")
    print("-" * 50)
    
    # Safety check
    confirmation = input(f"To confirm, please type the database name ('{DB_NAME}'): ")
    if confirmation.strip() != DB_NAME:
        print("Confirmation failed. Aborting restore.")
        return

    # Set the password for the command-line tool
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASSWORD

    # The pg_restore command
    # --clean: Drops database objects before recreating them.
    # --if-exists: Only drop objects if they exist (avoids errors).
    # -v: Verbose mode
    # -d: The database to connect to (must exist)
    command = [
        'pg_restore',
        '--clean',
        '--if-exists',
        '-v',
        '-h', DB_HOST,
        '-U', DB_USER,
        '-p', DB_PORT,
        '-d', DB_NAME,
        backup_file_path
    ]

    print("\nStarting database restore...")
    try:
        subprocess.run(command, check=True, env=env, capture_output=True, text=True)
        print(f"\nSUCCESS: Database restored successfully from '{backup_file_path}'!")
    except subprocess.CalledProcessError as e:
        print("\nERROR: pg_restore failed.")
        print(f"Command failed with exit code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print("\nERROR: 'pg_restore' command not found.")
        print("Please ensure PostgreSQL client tools are installed and in your system's PATH.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == '__main__':
    # Get the latest .dump file in the directory
    try:
        backup_files = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.dump')]
        if not backup_files:
            print("No backup files (.dump) found in the current directory.")
        else:
            latest_backup = max(backup_files, key=os.path.getctime)
            print(f"Found latest backup file: {latest_backup}")
            restore_from_backup(latest_backup)
    except Exception as e:
        print(f"Error finding backup files: {e}")

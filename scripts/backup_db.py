import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', '5432') # Default to 5432 if not set

# --- Backup File Naming ---
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BACKUP_FILENAME = f"backup_{TIMESTAMP}.dump"

def create_backup():
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print("Error: Database credentials are not fully configured in .env file.")
        return

    print(f"Starting backup of database '{DB_NAME}' from host '{DB_HOST}'...")

    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASSWORD

    # The pg_dump command
    # -F c: Use custom, compressed format
    # -Z 9: Use maximum compression
    # -v: Verbose mode
    
    # --no-privileges: Do not dump access privileges (GRANT/REVOKE).
    #                  This prevents non-portable permission errors on restore.
    command = [
        'pg_dump',
        '-F', 'c',
        '-Z', '9',
        '--no-privileges',
        '-v',
        '-h', DB_HOST,
        '-U', DB_USER,
        '-p', DB_PORT,
        '-d', DB_NAME,
        '-f', BACKUP_FILENAME
    ]

    try:
        subprocess.run(command, check=True, env=env, capture_output=True, text=True)
        print(f"\nSUCCESS: Database backup created successfully!")
        print(f"File saved as: {BACKUP_FILENAME}")
    except subprocess.CalledProcessError as e:
        print("\nERROR: pg_dump failed.")
        print(f"Command failed with exit code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print("\nERROR: 'pg_dump' command not found.")
        print("Please ensure PostgreSQL client tools are installed and in your system's PATH.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == '__main__':
    create_backup()

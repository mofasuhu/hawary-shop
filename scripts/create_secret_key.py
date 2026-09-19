import secrets
import string

def generate_secret_key(length=64):
    alphabet = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Generate and print the key
if __name__ == "__main__":
    secret_key = generate_secret_key()
    print(f"Your 64-character secret key:\n{secret_key}")

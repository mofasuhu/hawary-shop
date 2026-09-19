import re
from flask import g


def validate_username(username):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, username):
        return (
            False,
            g.translations["Invalid_email_address_format"],
        )
    return True, ""


def validate_password(password):
    # Rule 1: Check length (at least 8 characters)
    if len(password) < 8:
        return False, g.translations["Password_length_error"]

    # Rule 2: Check for spaces
    if re.search(r"\s+", password):
        return False, g.translations["Password_spaces_error"]

    # Rule 3: Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        return False, g.translations["Password_uppercase_error"]

    # Rule 4: Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        return False, g.translations["Password_lowercase_error"]

    # Rule 5: Check for at least one number
    if not re.search(r"[0-9]", password):
        return False, g.translations["Password_number_error"]

    # Rule 6: Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, g.translations["Password_special_char_error"]

    # If all checks pass
    return True, ""

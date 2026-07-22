from email_validator import validate_email, EmailNotValidError


def validate(email):

    try:

        validate_email(email)

        return True

    except EmailNotValidError:

        return False
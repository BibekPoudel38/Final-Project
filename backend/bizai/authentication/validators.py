from django.core.exceptions import ValidationError
import re

def validate_password(value):   
    """
    Custom password validator to enforce strong password rules.
    Modify the regex as needed.
    """
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    
    if not re.search(r'[A-Z]', value):
        raise ValidationError("Password must contain at least one uppercase letter.")
    
    if not re.search(r'[a-z]', value):
        raise ValidationError("Password must contain at least one lowercase letter.")
    
    if not re.search(r'[0-9]', value):
        raise ValidationError("Password must contain at least one digit.")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError("Password must contain at least one special character.")
    
    return value  # Return the valid password

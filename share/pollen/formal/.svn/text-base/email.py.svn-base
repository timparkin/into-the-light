import formal
from pollen.datastructures.email import validateEmailAddress

INVALID_EMAIL_FORMAT = "Invalid email address format"
def validateEmailField(field, value):

    if not validateEmailAddress(value):
        raise formal.FieldError(INVALID_EMAIL_FORMAT)


# Create a single email validator instance.
emailValidator = formal.CallableValidator(validateEmailField)


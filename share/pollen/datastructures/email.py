def validateEmailAddress(value):
    """
    Validate an email address.

    Note: using a regex to validate an email address is complex and error prone
    so let's just do something good enough and improve on it over time.
    """

    # Strip whitespace
    value = value.strip()

    # Spaces are not allowed
    if ' ' in value:
        return False

    # Split at the '@'.
    value = value.split('@')

    # There should only be two parts - the user account and domain name - and
    # they must both be present.
    if len([p for p in value if p]) != 2:
        return False

    userAccount, domainName = value

    # Check there are at least two parts to the domain name
    if len(domainName.split('.')) < 2:
        return False

    return True

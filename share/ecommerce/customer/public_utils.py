from nevow import tags as T
import formal

def addCoreFields(form, forCreation=False, billingCountryOptions=None, optInDescription=None, termsDescription=None):
    """
    Add customer fields to a form.
    """

    genderOptions = [(o,o) for o in ('male', 'female')]

    if forCreation:
        email = formal.String(required=True, strip=True)
        terms = formal.Boolean(required=True)
        password = formal.String(required=True, strip=True)
    else:
        email = formal.String(immutable=True)
        terms = formal.Boolean(immutable=True)
        password = formal.String(strip=True)

    form.add( formal.Field('email', email) )
    form.add( formal.Field('password', password, widgetFactory=formal.CheckedPassword) )
    form.add( formal.Field('gender', formal.String(required=True),
        widgetFactory=formal.widgetFactory(formal.SelectChoice, options=genderOptions)) )
    form.add( formal.Field('first_name', formal.String(required=True, strip=True)) )
    form.add( formal.Field('last_name', formal.String(required=True, strip=True)) )
    form.add( formal.Field('dateOfBirth', formal.Date(required=True),
        widgetFactory=formal.widgetFactory(formal.DatePartsInput, dayFirst=True)) )
    form.add( formal.Field('phoneNumber', formal.String(strip=True, required=True)) )
    form.add( formal.Field('billingAddress1', formal.String(required=True, strip=True), label='Billing Address Line 1') )
    form.add( formal.Field('billingAddress2', formal.String(strip=True), label='Billing Address Line 2') )
    form.add( formal.Field('billingAddress3', formal.String(strip=True), label='Billing Address Line 3') )
    form.add( formal.Field('billingCity', formal.String(required=True, strip=True), label='Billing City') )
    form.add( formal.Field('billingPostcode', formal.String(required=True, strip=True), label='Billing Postcode') )
    if billingCountryOptions:
        form.add( formal.Field('billingCountry', formal.String(required=True, strip=True), 
            formal.widgetFactory(formal.SelectChoice, options=billingCountryOptions), label='Billing Country') )
    else:
        form.add( formal.Field('billingCountry', formal.String(required=True, strip=True), label='Billing Country') )


    form.add( formal.Field('secretQuestion', formal.String(required=True, strip=True)) )
    form.add( formal.Field('secretAnswer', formal.String(required=True, strip=True)) )

    form.add( formal.Field('optIn', formal.Boolean(), description=optInDescription) )
    form.add( formal.Field('terms', terms, label="T's & C's", description=termsDescription) )



def getCoreFields(data):
    rv = {}
    rv['email'] = data['email']
    rv['password'] = data['password']
    rv['gender'] = data['gender']
    rv['first_name'] = data['first_name']
    rv['last_name'] = data['last_name']
    rv['dateOfBirth'] = data['dateOfBirth']
    rv['phoneNumber'] = data['phoneNumber']
    rv['billingAddress1'] = data['billingAddress1']
    rv['billingAddress2'] = data['billingAddress2']
    rv['billingAddress3'] = data['billingAddress3']
    rv['billingCity'] = data['billingCity']
    rv['billingPostcode'] = data['billingPostcode']
    rv['billingCountry'] = data.get('billingCountry')
    rv['secretQuestion'] = data['secretQuestion']
    rv['secretAnswer'] = data['secretAnswer']
    rv['optIn'] = data['optIn']
    rv['terms'] = data['terms']

    return rv



def getBillingCountryOptions(fileName):

    f = open(fileName, 'r')
    try:
        lines = f.readlines()
    finally:
        f.close()

    rv = []
    for line in lines:
        name, code = line[:-1].split(';')
        rv.append((code,name))

    return rv

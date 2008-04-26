from zope.interface import Interface



class INotificationService(Interface):


    def sendEmail(toAddresses, message, fromAddress=None, swallowErrors=None):
        pass


    def buildEmailFromTemplate(templateName, templateArgs, headers):
        pass


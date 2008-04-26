from types import GeneratorType
from zope.interface import implements
from twisted.mail import smtp
from twisted.python import log

from notification import errors, inotification



class NotificationService(object):

    implements(inotification.INotificationService)


    swallowSMTPErrors = True
    emailFromAddress = None


    def __init__(self, smtpHost, emailFromAddress=None, swallowSMTPErrors=None):
        self.smtpHost = smtpHost
        if emailFromAddress is not None:
            self.emailFromAddress = emailFromAddress
        if swallowSMTPErrors is not None:
            self.swallowSMTPErrors = swallowSMTPErrors


    def sendEmail(self, toAddresses, message, fromAddress=None, swallowErrors=None):
        """
        Send an email to one or more recipients.
        """

        # If toAddresses is not already a list type then make it so.
        if not isinstance(toAddresses, (list, tuple, GeneratorType)):
            toAddresses = [toAddresses]

        # Work out whether to swallow errors.
        if swallowErrors is None:
            swallowErrors = self.swallowSMTPErrors

        # Work out the from address to use.
        if fromAddress is None:
            fromAddress = self.emailFromAddress

        # Send the email
        d = smtp.sendmail(self.smtpHost, fromAddress, toAddresses, message)

        # Swallow smtp errors if requested
        if swallowErrors:
            d.addErrback(self._swallorSMTPError)

        # Remap SMTP errors
        d.addErrback(self._smtpError)

        # Return the result
        return d


    def buildEmailFromTemplate(self, templateName, templateArgs, headers):
        raise NotImplementedError("buildEmailFromTemplate must be "\
                "implemented by a subclass")


    def _swallorSMTPError(self, failure):
        failure.trap(smtp.SMTPDeliveryError)
        log.err(failure)


    def _smtpError(self, failure):
        failure.trap(smtp.SMTPDeliveryError)
        log.err(failure)
        raise errors.MailNotificationError(str(failure.value))


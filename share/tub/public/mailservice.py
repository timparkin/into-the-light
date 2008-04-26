from twisted.python import log
from twisted.mail import smtp
from twisted.mail.smtp import SMTPDeliveryError
from email.MIMEText import MIMEText

class MailException(Exception):
    pass


class MailService(object):

    failMailText = "There was an error: %(error)s"

    def __init__(self, siteId, config):
        self.siteId = siteId
        self.smtpServer = config['mailService']['smtpServer']

    def _sendmail(self, toAddress, fromAddress, msg):
        d = smtp.sendmail(self.smtpServer, fromAddress, toAddress, msg)
        d.addErrback(self._handleMailError)
        return d

    def _handleMailError(self, failure):
        log.err(failure)
        failure.trap(SMTPDeliveryError)
        raise MailException(str(failure.value))

    def sendMessage(self, toAddress, fromAddress, message):
        return self._sendmail(toAddress, fromAddress, message)


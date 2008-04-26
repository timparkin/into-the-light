from email.MIMEText import MIMEText
import os.path
from genshi.template import TextTemplate
from notification import service
from pollen.mail import emailbuilder



class NotificationService(service.NotificationService):


    def __init__(self, *a, **k):
        emailTemplateDir = k.pop("emailTemplateDir")
        super(NotificationService, self).__init__(*a, **k)
        self.emailTemplateDir = emailTemplateDir


    def buildEmailFromTemplate(self, templateName, templateArgs, headers):
        templateDir = os.path.join(self.emailTemplateDir, templateName)
        source = emailbuilder.FileSystemSource(templateDir)
        builder = TemplatedEmailBuilder(source, headers, templateArgs=templateArgs)
        return builder.build()



class TemplatedEmailBuilder(emailbuilder.EmailBuilder):


    def __init__(self, *a, **k):
        templateArgs = k.pop("templateArgs")
        super(TemplatedEmailBuilder, self).__init__(*a, **k)
        self.templateArgs = templateArgs


    def part_text(self, contentType, filename):
        template = TextTemplate(self.source[filename].read())
        stream = template.generate(**self.templateArgs)
        return MIMEText(stream.render("text"), contentType[1])



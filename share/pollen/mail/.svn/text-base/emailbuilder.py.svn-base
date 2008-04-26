import codecs
import os.path
import re
from email.MIMEMultipart import MIMEMultipart



PARTS = "parts.lst"



class EmailBuilderError(Exception):
    pass



class EmailBuilder(object):


    def __init__(self, source, headers):
        self.source = source
        self.headers = headers


    def build(self):

        # Create the main MIME message and add the headers.
        msg = MIMEMultipart()
        for k, v in self.headers.items():
            msg[k] = v

        # Create a stack of parts
        parts = [(None, msg)]

        # Open the parts file
        for line in self.source[PARTS]:
            # Parse the line
            indent, contentType, filename, args = self._parsePartLine(line)
            # Unpop the parts stack to get back to find the parent
            while indent <= parts[-1][0] and parts[-1][0] is not None:
                parts.pop()
            # Use the main type of the content type to find a factory for the part
            mainType = contentType[0]
            partFactory = getattr(self, "part_%s"%(mainType,), None)
            if partFactory is None:
                raise MailBuilderError("No factory for %r parts" % (mainType,))
            # Create the part and attach it to the parent part
            part = partFactory(contentType, filename)
            for k, v in args.items():
                part[k] = v
            parts[-1][1].attach(part)
            # Add this part to the stack so it's available to children
            parts.append((indent, part))

        return msg


    def part_multipart(self, contentType, filename):
        return MIMEMultipart(contentType[1])


    def part_text(self, contentType, filename):
        from email.MIMEText import MIMEText
        f = codecs.getreader("utf-8")(self.source[filename])
        try:
            return MIMEText(f.read(), contentType[1])
        finally:
            f.close()


    def part_image(self, contentType, filename):
        from email.MIMEImage import MIMEImage
        return MIMEImage(self.source[filename].read(), contentType[1])


    def part_application(self, contentType, filename):
        from email.MIMEApplication import MIMEApplication
        return MIMEApplication(self.source[filename].read(), contentType[1])


    def _parsePartLine(self, part):
        d = re.match("^(?P<indent> *?)(?P<contentType>[a-z]+/[a-z]+):(?P<rest>.*)$", part).groupdict()
        indent = len(d["indent"])
        contentType = tuple(d["contentType"].split("/"))
        rest = d["rest"].strip()
        if not rest:
            filename = None
            args = {}
        else:
            rest = rest.split(None)
            filename, args = rest[:1], rest[1:]
            filename = filename[0]
            args = dict([arg.split("=", 1) for arg in args])
        return indent, contentType, filename, args



class FileSystemSource(object):


    def __init__(self, dir):
        if not os.path.exists(dir) or not os.path.isdir(dir):
            raise EmailBuilderError("Invalid directory %r"%(dir,))
        self.dir = dir
        self.openFiles = []


    def __getitem__(self, name):
        f = file(os.path.join(self.dir, name))
        self.openFiles.append(f)
        return f


    def close(self):
        for f in self.openFiles:
            f.close()



def main():

    import sys
    from email.Utils import formatdate
    from smtplib import SMTP

    dir, from_, to_, subject_ = sys.argv[1:]

    headers = {
            "To": to_,
            "From": from_,
            "Subject": subject_,
            "Date": formatdate()
            }

    source = FileSystemSource(dir)
    try:
        msg = EmailBuilder(source, headers).build()
        SMTP("localhost").sendmail(from_, to_, str(msg))
    finally:
        source.close()



if __name__ == '__main__':
    main()


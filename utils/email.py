import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


class SMTP:
    def __init__(self, username: str, password: str, host: str, port: int, use_tls: bool = True):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.use_tls = use_tls

    def send(self, to: str, subject: str, attached_file: str):
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to
        msg['Subject'] = subject

        with open(attached_file, "rb") as attachment:
            part = MIMEApplication(attachment.read(), Name=attached_file)
            part['Content-Disposition'] = f'attachment; filename="{attached_file}"'
            msg.attach(part)

        server = smtplib.SMTP(self.host, self.port)
        if self.use_tls:
            server.starttls()
        server.login(self.username, self.password)
        server.sendmail(self.username, to, msg.as_string())
        server.quit()

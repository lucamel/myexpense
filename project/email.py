# project/email.py
from threading import Thread
from flask_mail import Message

from . import app, mail


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)

class AsyncEmail(Thread):
    def __init__(self, to, subject, template):
        Thread.__init__(self)
        self.to = to
        self.subject = subject
        self.template = template

    def run(self):
        print("Inizio invio email: "+self.subject)
        with app.app_context():
            msg = Message(
                self.subject,
                recipients=[self.to],
                html=self.template,
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            mail.send(msg)
            print("Email inviata.")

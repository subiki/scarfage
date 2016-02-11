import smtplib
import html2text

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail(recipient, subject, message, sender=None):
    if sender is None:
        sender = 'Scarfage <do_not_reply@scarfage.com>'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    text = html2text.html2text(message)

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(message, 'html')

    msg.attach(part1)
    msg.attach(part2)

    s = smtplib.SMTP('localhost')
    s.sendmail(sender, recipient, msg.as_string())
    s.quit()

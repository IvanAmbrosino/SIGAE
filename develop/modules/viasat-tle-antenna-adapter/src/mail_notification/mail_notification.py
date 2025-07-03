"""Modulo de envio de mails -> Tomado prestado de Ebaum"""
__author__ = "Emiliano A. Baum"
__version__ = "0, Envia mail de notificacion"
__last_revision__ = "2020-01-30"

from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import logging


logger = logging.getLogger("mail sender")

class SendNotification():
    """Clase encargada de las notificaciones de mail"""
    def __init__(self,):
        logger.info("Inicia el envio de mail para el archivo.")
        self.msg = MIMEMultipart()

    def run(self, mail_config, tle, msg):
        """Envia el mail de notificacion de cada archivo procesado"""
        logger.info("Cargando variable para el envio de mail")
        self.msg['From'] = mail_config["from"]
        self.msg['To'] = (', ').join(mail_config["to"])
        self.msg['Date'] = formatdate(localtime=True)
        self.msg['Subject'] = 'TEST - Mail Error AtualizaTLE - Viasat TLE Sender'

        body = f"Error procesando el TLE:\n\n{tle}\n\nMensaje de error:\n{msg}"
        self.msg.attach(MIMEText(body, 'plain'))

        logger.info("Conectando a %s.", mail_config['mailserver'])
        with SMTP(mail_config['mailserver']) as smtp:
            smtp.set_debuglevel(1)
            smtp.sendmail(self.msg['From'], mail_config["to"],
                          self.msg.as_string())
            smtp.quit()
        logger.info("Termina de enviar el mail para el tle: %s", tle)

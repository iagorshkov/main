import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_news():
	with open('config.json', 'r') as file:
		PASSWORD = json.loads(file.read())['e-mail_password']
	msg = MIMEMultipart()
	msg['Subject'] = 'News dump' 
	msg['From'] = 'onobot_2'
	msg['To'] = 'iagorshkov310@gmail.com'

	part = MIMEBase('application', "octet-stream")
	part.set_payload(open("data/all_data.csv", "rb").read())
	encoders.encode_base64(part)

	part.add_header('Content-Disposition', 'attachment; filename="all_data.csv"')
#####
	part2 = MIMEBase('application', "octet-stream")
	part2.set_payload(open("data/news.csv", "rb").read())
	encoders.encode_base64(part2)

	part2.add_header('Content-Disposition', 'attachment; filename="news.csv"')

	msg.attach(part)
	msg.attach(part2)

	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login('iagorshkov310',PASSWORD)
	server.sendmail('onobot_2', 'iagorshkov310@gmail.com', msg.as_string())
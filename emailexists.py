import dns.resolver
import pdb
import argparse
from smtplib import SMTP

parser = argparse.ArgumentParser(
    description='Checks if email address is valid a la Mailtester.com')
parser.add_argument('email', help='the email address to check')
args = parser.parse_args()
domain = args.email.split('@')[1]

dig_resp = dns.resolver.query(domain, 'MX')
mx_servers = []
for d in dig_resp:
    mx_servers.append((d.preference, str(d.exchange)))
mx_servers.sort()

print('Using server with lowest priority', mx_servers[0])
mailserver = SMTP(mx_servers[0][1])
helo_resp = mailserver.helo()
print(helo_resp)

if helo_resp[1].decode().find('mail.protection.outlook.com') != -1:
    print('Microsoft SMTP servers will ban this IP')
else:
    print(mailserver.docmd('MAIL', args='FROM:<bob@example.org>'))
    print(mailserver.docmd('RCPT', args='TO:<' + args.email + '>'))
    print(mailserver.docmd('QUIT'))

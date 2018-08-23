import smtplib
import argparse
import socket

def send_email(from_address, password, to_address, subject, text, smtp_server):
    smtp_host, smtp_port = smtp_server.split(':')
    server = smtplib.SMTP(smtp_host, smtp_port)
    if from_address.lower().endswith('@gmail.com'):
        server.ehlo()
    server.starttls()
    server.login(from_address, password)
    body = '\r\n'.join([
        f'To: {to_address}',
        f'From: {from_address}',
        f'Subject: {subject}',
        '', text
    ])

    try:
        server.sendmail(from_address, [to_address], body)
        print('email sent')
    except:
        import sys
        print('error sending email', file=sys.stderr)
    server.quit()

def main():
    parser = argparse.ArgumentParser()
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument('-u', '--username', help='the sender email address', required=True)
    required_args.add_argument('-p', '--password', help='the password for the sender email account', required=True)
    required_args.add_argument('-t', '--to', help='the recipient email address', required=True)
    required_args.add_argument('-s', '--server', help='the SMTP server for the sender email', required=True)
    args = parser.parse_args()
    from_address = args.username
    password = args.password
    to_address = args.to
    smtp_server = args.server
    hostname = socket.gethostname()
    subject = f'Error Crawling Snapshot on {hostname}'
    with open('err.txt', 'r') as f:
        text = f.read()
    send_email(from_address, password, to_address, subject, text, smtp_server)

if __name__ == '__main__':
    main()

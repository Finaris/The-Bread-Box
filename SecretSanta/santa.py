import csv
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def get_member_info(filename):
    with open(filename, 'r') as file:
        csv_file = csv.DictReader(file)

        # yield all name, kerb, non-pair groups that are participating
        for line in csv_file:
            if line['participating'] == 'Yes':
                # separate non_pair members into a set
                yield (line['name'].strip(),
                       line['kerberos'].strip(),
                       set(filter(lambda x: x, line['non_pairs'].split('; '))))


def get_server_instance(user, password):
    # login to gmail server/account
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(user, password)

    return server


def send_email(server, user, recipient, subject, message):
    # send email's message with a formatted header
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = user
    msg['To'] = recipient
    msg.attach(message)
    server.sendmail(user, recipient, msg.as_string())


def assign_members(members):
    # set seed, in case we need to repeat for a subset
    random.seed(2018)
    assignees = [member[0] for member in members]
    no_pair_map = {member[0]: member[-1] for member in members}

    # shuffle names until valid assignment is found
    finished = False
    while not finished:
        random.shuffle(assignees)

        finished = True
        for i in range(len(assignees)):
            # make sure that nobody is assigned to someone in their no pairs
            if assignees[(i + 1) % len(assignees)] in no_pair_map[assignees[i]]:
                finished = False
                break

    # format assignments into pairs
    return {assignees[i]: assignees[(i + 1) % len(members)] for i in range(len(members))}


def main():
    # load members and their assignments
    message_text = open('message.txt').read()

    members = list(get_member_info('fake_members.csv'))
    assignment = assign_members(members)

    print(members)
    print(assignment)

    # start smtp server
    user = 'g1ng3rbr34db0x@gmail.com'
    password = ''  # fill in before running code
    server = get_server_instance(user, password)

    # send out personalized emails
    for member in members:
        message = MIMEText(message_text.format(member[0], assignment[member[0]]), 'html')
        send_email(server,
                   user,
                   member[1] + '@mit.edu',
                   'Secret Santa Assignment',
                   message)

    server.quit()


if __name__ == '__main__':
    main()

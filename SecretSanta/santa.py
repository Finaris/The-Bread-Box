import csv
import random
import smtplib


MAIN_MESSAGE = "Hey {0:}, \r\n" + \
               "Happy (upcoming) holiday season! This is Santa, with your Secret Santa assignment! " + \
               "You have been assigned {1:}, so you will need to make, find, buy, or steal them a" + \
               " gift in time for our Secret Santa party, which we are tentatively scheduling for" + \
               " the night of December 14th, but we will probably vote on later. Please try to " + \
               "limit your gift to a $10 - $20 price range, whether that is for the gift itself " + \
               "or materials used to make the gift. This is so that nobody feels pressured to " + \
               "spend too much, as this is supposed to be fun!\r\n\n" + \
               "We will be planning the details of the Secret Santa Party later this month, but" + \
               " feel free to start thinking of snacks, games, and other activities that you " + \
               "may want at the party. If you have any ideas you're excited about, or if there is " + \
               "something wrong with this automated message, please let Collin know.\r\n\n" + \
               "Happy Holidays,\r\nSanta Claus"


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
    message_header = 'From: %s\r\nTo: %s\r\nSubject: %s\r\n' % (user, recipient, subject)
    server.sendmail(user, recipient, message_header + message)


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
        message = MAIN_MESSAGE.format(member[0], assignment[member[0]])
        send_email(server,
                   user,
                   member[1] + '@mit.edu',
                   'Secret Santa Assignment',
                   message)


if __name__ == '__main__':
    main()

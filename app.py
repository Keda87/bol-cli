#!/usr/bin/env python
import sys
import argparse
from getpass import getpass
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

try:
    driver = webdriver.PhantomJS()
except:
    driver = None

try:
    input = raw_input
except NameError:
    pass


class Password(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            values = getpass()
        setattr(namespace, self.dest, values)


parser = argparse.ArgumentParser(description='Binus Online command line interface.')
required_named = parser.add_argument_group('required named arguments')
required_named.add_argument('-u', help='your BOL email', type=str, dest='email')
required_named.add_argument('-p', action=Password, nargs='?', dest='password', help='enter your password')
args = parser.parse_args()


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
def has_colours(stream):
    # Reference: http://blog.mathieu-leplatre.info/colored-output-in-console-with-python.html
    if not hasattr(stream, 'isatty'):
        return False
    if not stream.isatty():
        return False  # auto color only on TTYs
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum('colors') > 2
    except:
        # guess false in case of error
        return False
has_colours = has_colours(sys.stdout)


def printout(text, colour=WHITE):
    if has_colours:
        seq = '\x1b[1;%dm' % (30 + colour) + text + '\x1b[0m'
        sys.stdout.write(seq)
    else:
        sys.stdout.write(text)


def login(email, password):
    driver.get('https://ol.binus.ac.id/LoginBinusian')
    driver.find_element_by_id('TextBoxID').send_keys(email)
    driver.find_element_by_id('TxtPassword').send_keys(password)
    driver.find_element_by_id('ButtonLogin').click()
    return driver


def get_list_notifications():
    driver.get('https://ol.binus.ac.id/Services/ViewNotification.aspx')
    elements = driver.find_elements_by_xpath('//div[@class="notification unread"]')
    notifications = []
    for i in elements:
        credential = i.find_element_by_class_name('credentials')
        anchor = credential.find_element_by_tag_name('a')
        date = credential.find_element_by_class_name('date')
        notifications.append({
            'name': anchor.text,
            'date': date.text,
            'url': anchor.get_attribute('href')
        })
    return notifications


def open_thread(url):
    driver.get(url)
    content = driver.find_element_by_id('MainContent_rptThreadView_lblPostContent_0').text
    return content


def app(email, password):
    dashboard = login(email, password)
    try:
        name = dashboard.find_element_by_id('MainContent_UCStudentLoginProfile1_LabelStudentName').text
        total_notif = int(dashboard.find_element_by_class_name('notif-count').text)

        welcome = ('Welcome to BOL (Binus Online) CLI.\n'
                   'Hello {name}, you have {notif} unread {plural}:\n')
        plural = 'notifications' if total_notif > 1 else 'notification'
        welcome = welcome.format(name=name, notif=total_notif, plural=plural)
        printout(welcome)

        # Getting all unread notifications.
        notifications = get_list_notifications()
        printout('')
        while True:
            for index, notification in enumerate(notifications, start=1):
                notification.update({'index': index})
                notif = '[{index}] {name} at {date}\n'.format(**notification)
                printout(notif, GREEN)
            try:
                user_input = int(input('Choose an options above to open thread: ')) - 1
                url = notifications[user_input]['url']
            except:
                printout('Invalid thread options.\n', RED)
                driver.quit()
                break
            else:
                printout('\n' + open_thread(url) + '\n', MAGENTA)
    except NoSuchElementException:
        printout('Invalid email or password combination.\n', RED)
        driver.quit()


if __name__ == '__main__':
    if driver:
        try:
            if not (args.email and args.password):
                raise ValueError
            app(email=args.email, password=args.password)
        except KeyboardInterrupt:
            printout('Bye..\n', GREEN)
            driver.quit()
        except ValueError:
            printout('Email and Password are required through arguments.\n', RED)
            driver.quit()
    else:
        printout('PhantomJS is not installed. (http://phantomjs.org/)\n', RED)

#!/usr/bin/env python
import argparse
from getpass import getpass
from typing import Tuple, AnyStr, List, Dict

from requests_html import HTML
from robobrowser import RoboBrowser


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


def login(email: AnyStr, password: AnyStr) -> Tuple[RoboBrowser, HTML]:
    browser = RoboBrowser()
    browser.open('https://ol.binus.ac.id/LoginBinusian')

    login_form = browser.get_form(class_='custom-form')
    login_form['TextBoxID'] = email
    login_form['TxtPassword'] = password

    browser.submit_form(form=login_form)
    content = browser.response.content
    return browser, HTML(html=content)


def get_notifications(browser_obj: RoboBrowser) -> Tuple[RoboBrowser, List[Dict[AnyStr, AnyStr]]]:
    browser_obj.open(url='https://ol.binus.ac.id/Services/ViewNotification.aspx')
    response = browser_obj.response.content
    response = HTML(html=response)
    elements = response.find('div.notification.unread')
    notifications = []
    for i in elements:
        credential = i.find('div.credentials', first=True)
        anchor = credential.find('a', first=True)
        date = credential.find('span.date', first=True)
        href = anchor.attrs.get('href')
        notifications.append({
            'name': anchor.text,
            'date': date.text,
            'url': f'https://ol.binus.ac.id{href}'
        })
    return browser_obj, notifications


def open_thread(browser_obj: RoboBrowser, url: AnyStr) -> AnyStr:
    browser_obj.open(url=url)
    response = browser_obj.response.content
    response = HTML(html=response)
    content = response.find('span#MainContent_rptThreadView_lblPostContent_0', first=True)
    return content.text


def main(email: AnyStr, password: AnyStr) -> None:
    try:
        if not (args.email and args.password):
            raise ValueError

        browser, dashboard = login(email, password)

        name = dashboard.find('span#LblStudentName1', first=True).text
        notif_count = dashboard.find('span#dataCount', first=True).text
        notif_count = int(notif_count)
        plural = 'notifications' if notif_count > 1 else 'notification'

        welcome = f"""
        Welcome to BOL (Binus Online) CLI.
        Hello {name}, you have {notif_count} unread {plural}
        """
        print(welcome)

        # Getting all unread notifications.
        browser, notifications = get_notifications(browser_obj=browser)
        print('')
        while True:
            for index, notification in enumerate(notifications, start=1):
                notification.update({'index': index})
                notif = '[{index}] {name} at {date}\n'.format(**notification)
                print(notif)

            try:
                user_input = input('Choose an options above to open thread: ')
                user_input = int(user_input) - 1
                url = notifications[user_input]['url']

                thread = open_thread(browser_obj=browser, url=url)
                print(f'\n{thread}\n')
            except IndexError:
                print('Invalid options.\n')
    except KeyboardInterrupt:
        print('Bye..')
    except ValueError:
        print('Email and Password are required through arguments.\n')
    except AttributeError:
        print('Invalid email and password combination.\n')


if __name__ == '__main__':
    main(email=args.email, password=args.password)

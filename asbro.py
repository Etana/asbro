#!/usr/bin/env python

from io import BytesIO
from lxml import etree
import requests
import sys
import urllib

s = requests.Session()

DEFAULT_PAGE = 'https://www.google.com'
IGNORED_TAGS = {'html', 'head', 'body', 'meta', 'link', 'script', 'style'}

def browse_page(actions):
    """ Ask url and browse it """
    url = input('{}\nbrowse to ({}) ? '.format('<' * 80, DEFAULT_PAGE)) or DEFAULT_PAGE
    print('>' * 80)
    if url == 'exit':
        sys.exit(0)
    method = 'get'
    data = {}
    # a digit url is an action
    if url.isdigit() and int(url) in actions:
        action = actions[int(url)]
        # either a form to send action
        if isinstance(action, dict):
            url = action['action']
            method = action['method']
            for field_name, default in action['fields'].items():
                data[field_name] = input('{} ({}) ? '.format(field_name, default)) or default
        # or a link to follow
        else:
            url = action

    # get page content
    page_content = getattr(s, method)(url, data=data, stream=True).text

    # parse page and display content
    level = 0
    action_num = 1
    actions = {}
    form = None
    for action, elem in etree.iterparse(BytesIO(page_content.encode('utf-8')), events=("start", "end",), html=True):
        if elem.tag in IGNORED_TAGS:
            continue
        if action == 'start':
            # form tag
            if elem.tag == 'form':
                form = {
                    'action': urllib.parse.urljoin(url, elem.get('action')),
                    'method': elem.get('method', 'get').lower(),
                    'fields': {}
                }
            # input tag inside form tag
            if form and elem.tag == 'input' and 'name' in elem.attrib:
                form['fields'][elem.attrib['name']] = elem.get('value')
            # text inside tag
            if elem.text and elem.text.strip():
                if elem.tag == 'a' and 'href' in elem.attrib:
                    elem_action = action_num
                    actions[elem_action] = urllib.parse.urljoin(url, elem.attrib['href'])
                    action_num += 1
                else:
                    elem_action = None
                print('{}{}{}'.format(' '*level, elem.text.strip(), ' (#'+str(elem_action)+')' if elem_action else ''))
            level += 1
        else:
            # end of form tag
            if elem.tag == 'form' and form:
                elem_action = action_num
                actions[elem_action] = form
                print('{}FORM #{} : {} {} with fields {}'.format(' '*level, elem_action, form['method'], form['action'], form['fields']))
                action_num += 1
                form = None
            level -= 1
            # text after end of tag
            if elem.tail and elem.tail.strip():
                print('{}{}'.format(' '*level, elem.tail.strip()))
    return actions

# loop on page browsing
actions = {}
while True:
    actions = browse_page(actions)

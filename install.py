# -*- coding: utf-8 -*-
"""
Pythonista Action Deck installer.

Paste this into Pythonista and run it, or run this file directly.
"""

from __future__ import print_function

import os
import urllib.request

import editor


SOURCE_URL = (
    'https://raw.githubusercontent.com/'
    'jackatttack/pythonista-action-deck/main/action_deck.py'
)

INSTALL_FOLDER = os.path.expanduser(
    '~/Documents/Pythonista Action Deck'
)

INSTALL_PATH = os.path.join(
    INSTALL_FOLDER,
    'action_deck.py'
)


def main():
    os.makedirs(INSTALL_FOLDER, exist_ok=True)

    print('Downloading Pythonista Action Deck...')
    urllib.request.urlretrieve(SOURCE_URL, INSTALL_PATH)

    print('Installed:')
    print(INSTALL_PATH)
    print()
    print('Add action_deck.py to Pythonista\'s wrench menu.')

    editor.open_file(INSTALL_PATH)


if __name__ == '__main__':
    main()
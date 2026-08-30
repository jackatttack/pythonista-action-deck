# -*- coding: utf-8 -*-
"""
Pythonista Action Deck
======================

A fast, touch-friendly editor utility panel for Pythonista on iPhone and iPad.

Action Deck is designed to be launched from Pythonista's wrench/action menu
while another script is open. It acts on that active editor script.

Features:
- copy the active script or its path
- create Pythonista run or open URLs
- replace, append, clear, or duplicate the active script
- inspect and edit the clipboard
- find and replace text in the active script
- swipe between pages or use the bottom tabs
- tap ? to swap action names for plain-English descriptions

The app is intentionally self-contained:
- no .pyui file
- no external dependencies
- no project-specific integrations
"""

from __future__ import print_function

import os

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

import ui
import editor
import clipboard
try:
    from objc_util import ObjCClass, sel
except Exception:
    ObjCClass = None
    sel = None

try:
    import console
except Exception:
    console = None


# ============================================================
# Editable appearance
# ============================================================

BG_COLOR = '#0F1319'
HELP_CARD_COLOR = '#1D3150'
HELP_TEXT_COLOR = '#E8F1FF'

CARD_BORDER_COLOR = '#293443'
HELP_BORDER_COLOR = '#42699D'
TAB_ACTIVE_COLOR = '#213454'
HELP_BUTTON_COLOR = '#213454'

INPUT_BG_COLOR = '#F4F6FA'
INPUT_TEXT_COLOR = '#171B22'

CARD_COLOR = '#1B222C'
CARD_2_COLOR = '#151B23'
TEXT_COLOR = '#F4F7FB'
MUTED_COLOR = '#9BA7B7'
ACCENT_COLOR = '#6596FF'
WARN_COLOR = '#FFC857'
DELETE_COLOR = '#FF6B72'

FONT_NAME = 'AvenirNext-DemiBold'
FONT_SIZE = 17
DESCRIPTION_FONT_SIZE = 14
SMALL_FONT_SIZE = 13

PADDING = 12
ROW_HEIGHT = 64
ROW_SPACING = 10
ROW_RADIUS = 12

HEADER_HEIGHT = 84
TAB_BAR_HEIGHT = 78

INPUT_HEIGHT = 44
INPUT_RADIUS = 10

ROOT = os.path.expanduser('~/Documents')


# ============================================================
# Active editor helpers
# ============================================================

def dismiss_system_keyboard():
    """
    Ask iOS itself to resign whichever control currently owns the keyboard.

    Pythonista's high-level ui.View editing helpers are not reliable for every
    TextView/TextField configuration, so keyboard dismissal goes directly
    through UIKit when objc_util is available.
    """
    if ObjCClass is None or sel is None:
        return False

    try:
        application = ObjCClass('UIApplication').sharedApplication()

        # This sends resignFirstResponder to whichever control currently owns
        # keyboard focus, without needing to know whether it is a TextView or
        # TextField.
        if application.sendAction_to_from_forEvent_(
            sel('resignFirstResponder'),
            None,
            None,
            None
        ):
            return True
    except Exception:
        pass

    # Fallback for cases where the responder-chain action is unavailable.
    try:
        application = ObjCClass('UIApplication').sharedApplication()

        windows = []

        try:
            key_window = application.keyWindow()
            if key_window:
                windows.append(key_window)
        except Exception:
            pass

        try:
            for window in application.windows():
                if window:
                    windows.append(window)
        except Exception:
            pass

        for window in windows:
            try:
                window.endEditing_(True)
                return True
            except Exception:
                pass
    except Exception:
        pass

    return False

def hud(message, style='success', duration=1.0):
    """Show a short Pythonista HUD message, with a print fallback."""
    try:
        if console:
            console.hud_alert(str(message), style, duration)
        else:
            print('[Action Deck]', message)
    except Exception:
        print('[Action Deck]', message)


def active_path():
    """Return the filesystem path of the currently open editor file."""
    try:
        return editor.get_path() or ''
    except Exception:
        return ''


def active_text():
    """Return the current editor buffer exactly as Pythonista sees it."""
    try:
        return editor.get_text() or ''
    except Exception:
        return ''


def active_rel_path():
    """
    Return the active path relative to Pythonista's Documents folder.

    An empty string means the file is not inside ~/Documents, so it cannot
    safely be represented as a normal Pythonista run URL.
    """
    path = active_path()
    if not path:
        return ''

    try:
        relative = os.path.relpath(path, ROOT)
    except Exception:
        return ''

    if relative == '..' or relative.startswith('..' + os.sep):
        return ''

    return relative.replace(os.sep, '/')


def active_name():
    """Return the current filename, or a friendly fallback."""
    path = active_path()
    return os.path.basename(path) if path else 'editor-buffer.py'


def replace_active_text(text):
    """Replace the complete active editor buffer."""
    try:
        current = editor.get_text() or ''
        editor.replace_text(0, len(current), text or '')
        return True
    except Exception as error:
        hud('Replace failed: %s' % error, 'error', 1.2)
        return False


def append_to_active_text(text):
    """Append text to the active editor buffer using one sensible newline."""
    current = active_text()
    addition = text or ''

    if not addition:
        return True

    joiner = '' if not current or current.endswith('\n') else '\n'
    return replace_active_text(current + joiner + addition)


# ============================================================
# Clipboard and file helpers
# ============================================================

def copy_text(text, message='Copied'):
    """Copy text and show a small confirmation."""
    clipboard.set(text or '')
    hud(message)


def clean_text(text):
    """Normalise newlines and remove trailing whitespace."""
    text = text or ''
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines).strip()


def clean_clipboard_text():
    """Clean the current clipboard text and save the cleaned result."""
    cleaned = clean_text(clipboard.get() or '')
    clipboard.set(cleaned)
    return cleaned


def pythonista_script_url(action):
    """
    Build a Pythonista URL for the active script.

    Supported actions:
    - run: open Pythonista and run the script
    - open: open the script in Pythonista's editor
    """
    if action not in ('run', 'open'):
        return ''

    relative = active_rel_path()
    if not relative:
        return ''

    encoded_path = quote(relative, safe='/')
    return 'pythonista3://%s?action=%s' % (encoded_path, action)

def pythonista_run_url():
    """Build a Pythonista URL that runs the active script."""
    return pythonista_script_url('run')

def pythonista_open_url():
    """Build a Pythonista URL that opens the active script for editing."""
    return pythonista_script_url('open')


def next_duplicate_path(path):
    """
    Find a free sibling filename for a duplicate.

    example.py
        -> example_copy.py
        -> example_copy_2.py
        -> example_copy_3.py
    """
    folder = os.path.dirname(path)
    filename = os.path.basename(path)
    stem, extension = os.path.splitext(filename)

    first = os.path.join(folder, stem + '_copy' + extension)
    if not os.path.exists(first):
        return first

    number = 2
    while True:
        candidate = os.path.join(
            folder,
            '%s_copy_%d%s' % (stem, number, extension)
        )
        if not os.path.exists(candidate):
            return candidate
        number += 1


def duplicate_active_script():
    """
    Create a copy of the current editor buffer beside the original file.

    The editor buffer is used rather than copying the file from disk, so
    unsaved edits are included in the duplicate.
    """
    path = active_path()
    if not path:
        hud('No open script', 'error')
        return ''

    destination = next_duplicate_path(path)

    try:
        with open(destination, 'w', encoding='utf-8') as handle:
            handle.write(active_text())
    except TypeError:
        with open(destination, 'w') as handle:
            handle.write(active_text())
    except Exception as error:
        hud('Duplicate failed: %s' % error, 'error', 1.2)
        return ''

    hud('Created %s' % os.path.basename(destination))
    return destination


def confirm_clear_script():
    """Ask before removing every character from the active script."""
    if console:
        try:
            result = console.alert(
                'Clear Script',
                'Remove all text from the open script?',
                'Clear',
                'Cancel',
                hide_cancel_button=True
            )
            return result == 1
        except Exception:
            pass

    return True


# ============================================================
# Reusable action row
# ============================================================

class ActionRow(ui.View):
    """
    One large touch target.

    Every row has:
    - a short normal label
    - a plain-English description

    RootApp can switch all rows between the two with the ? button.
    """

    def __init__(
        self,
        title,
        description,
        on_tap,
        tint=TEXT_COLOR
    ):
        super().__init__()

        self.background_color = CARD_COLOR
        self.corner_radius = ROW_RADIUS
        self.border_width = 1
        self.border_color = CARD_BORDER_COLOR

        self.title_text = title
        self.description_text = description
        self.normal_tint = tint
        self._on_tap = on_tap
        self._help_mode = False

        self._label = ui.Label(
            text=title,
            text_color=tint,
            font=(FONT_NAME, FONT_SIZE),
            alignment=ui.ALIGN_LEFT
        )

        try:
            self._label.number_of_lines = 2
        except Exception:
            pass

        self.add_subview(self._label)

        self._overlay = ui.View(
            background_color=ACCENT_COLOR,
            alpha=0
        )
        self._overlay.corner_radius = ROW_RADIUS
        self.add_subview(self._overlay)

    def layout(self):
        self._label.frame = (
            PADDING,
            0,
            self.width - 2 * PADDING,
            self.height
        )
        self._overlay.frame = self.bounds

    def set_help_mode(self, enabled):
        self._help_mode = bool(enabled)

        if self._help_mode:
            self.background_color = HELP_CARD_COLOR
            self.border_color = HELP_BORDER_COLOR
            self._label.text = self.description_text
            self._label.font = (FONT_NAME, DESCRIPTION_FONT_SIZE)
            self._label.text_color = HELP_TEXT_COLOR
        else:
            self.background_color = CARD_COLOR
            self.border_color = CARD_BORDER_COLOR
            self._label.text = self.title_text
            self._label.font = (FONT_NAME, FONT_SIZE)
            self._label.text_color = self.normal_tint

    def touch_began(self, touch):
        self._overlay.alpha = 0.15

    def touch_moved(self, touch):
        pass

    def touch_ended(self, touch):
        self._overlay.alpha = 0

        if callable(self._on_tap):
            self._on_tap()

    def touch_cancelled(self, touch):
        self._overlay.alpha = 0


# ============================================================
# Base scrolling action page
# ============================================================

class RowsPage(ui.View):
    title = ''

    def __init__(self, root):
        super().__init__()

        self.background_color = BG_COLOR
        self.root = root

        self.scroll = ui.ScrollView(background_color=BG_COLOR)
        self.scroll.shows_vertical_indicator = True

        self._scroll_delegate = KeyboardDismissScrollDelegate(root)
        self.scroll.delegate = self._scroll_delegate

        self.add_subview(self.scroll)

        self._built = False

    def layout(self):
        self.scroll.frame = self.bounds

        if not self._built:
            self.build_rows()
            self._built = True

        y = PADDING

        for row in self.scroll.subviews:
            row.frame = (
                PADDING,
                y,
                self.width - 2 * PADDING,
                ROW_HEIGHT
            )
            y += ROW_HEIGHT + ROW_SPACING

        self.scroll.content_size = (
            self.width,
            max(y + PADDING, self.height + 1)
        )

    def add_row(
        self,
        title,
        description,
        callback,
        tint=TEXT_COLOR
    ):
        row = ActionRow(
            title,
            description,
            callback,
            tint=tint
        )
        row.set_help_mode(self.root.help_mode)
        self.scroll.add_subview(row)
        return row

    def set_help_mode(self, enabled):
        for row in self.scroll.subviews:
            if isinstance(row, ActionRow):
                row.set_help_mode(enabled)

    def close_after(self, delay=0.05):
        ui.delay(self.root.close, delay)

    def build_rows(self):
        pass


# ============================================================
# Quick page
# ============================================================

class QuickPage(RowsPage):
    title = 'Quick'

    def build_rows(self):
        self.add_row(
            '📋 Copy Script',
            'Copy the entire open script to the clipboard.',
            self._copy_script
        )

        self.add_row(
            '📂 Copy Path',
            'Copy the full filesystem path of the open script.',
            self._copy_path
        )

        self.add_row(
            '▶️ Copy Run URL',
            'Copy a pythonista3:// URL that runs the open script.',
            self._copy_run_url
        )

        self.add_row(
            '📝 Copy Open URL',
            'Copy a pythonista3:// URL that opens the script for editing.',
            self._copy_open_url
        )

        self.add_row(
            '📥 Replace with Clipboard',
            'Replace the whole open script with the clipboard contents.',
            self._replace_with_clipboard,
            tint=WARN_COLOR
        )

        self.add_row(
            '📄 Duplicate Script',
            'Create a numbered copy beside the current script.',
            self._duplicate_script
        )

        self.add_row(
            '🗑️ Clear Script',
            'Remove all text from the open script after confirmation.',
            self._clear_script,
            tint=DELETE_COLOR
        )

    def _copy_script(self):
        copy_text(active_text(), 'Script copied')
        self.close_after()

    def _copy_path(self):
        path = active_path()

        if path:
            copy_text(path, 'Path copied')
        else:
            hud('No open script', 'error')

        self.close_after()

    def _copy_run_url(self):
        url = pythonista_run_url()

        if url:
            copy_text(url, 'Run URL copied')
        else:
            hud('Run URL unavailable for this file', 'error', 1.2)

        self.close_after()

    def _copy_open_url(self):
        url = pythonista_open_url()

        if url:
            copy_text(url, 'Open URL copied')
        else:
            hud('Open URL unavailable for this file', 'error', 1.2)

        self.close_after()

    def _replace_with_clipboard(self):
        if replace_active_text(clipboard.get() or ''):
            hud('Script replaced')
        self.close_after()

    def _append_clipboard(self):
        if append_to_active_text(clipboard.get() or ''):
            hud('Clipboard appended')
        self.close_after()

    def _duplicate_script(self):
        duplicate_active_script()
        self.close_after()

    def _clear_script(self):
        if not confirm_clear_script():
            return

        if replace_active_text(''):
            hud('Script cleared')

        self.close_after()


# ============================================================
# Clipboard editor page
# ============================================================

class ClipboardPage(ui.View):
    title = 'Clipboard'

    def __init__(self, root):
        super().__init__()

        self.background_color = BG_COLOR
        self.root = root
        self._loaded_once = False

        self.textview = ui.TextView()
        self.textview.background_color = CARD_COLOR
        self.textview.text_color = TEXT_COLOR
        self.textview.tint_color = ACCENT_COLOR
        self.textview.font = ('Menlo', 15)
        self.textview.corner_radius = ROW_RADIUS

        try:
            self.textview.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
            self.textview.autocorrection_type = False
            self.textview.spellchecking_type = False
        except Exception:
            pass

        self.add_subview(self.textview)

        self.scroll = ui.ScrollView(background_color=BG_COLOR)
        self.scroll.shows_vertical_indicator = True
        self.add_subview(self.scroll)

        self.keyboard_button = ui.Button(
            title='⌨︎↓',
            font=(FONT_NAME, 17),
            tint_color=ACCENT_COLOR,
            background_color=CARD_2_COLOR
        )
        self.keyboard_button.corner_radius = 9
        self.keyboard_button.action = self._dismiss_keyboard
        self.add_subview(self.keyboard_button)
        # Scrolling the action list should dismiss the keyboard. The TextView itself
        # intentionally keeps its normal scrolling behaviour.
        self._scroll_delegate = KeyboardDismissScrollDelegate(root)
        self.scroll.delegate = self._scroll_delegate
        self._rows_built = False

    def layout(self):
        editor_height = max(
            190,
            int(self.height * 0.38)
        )

        self.textview.frame = (
            PADDING,
            PADDING,
            self.width - 2 * PADDING,
            editor_height
        )

        # A small always-visible escape hatch for Pythonista's keyboard.
        self.keyboard_button.frame = (
            self.width - PADDING - 52,
            PADDING + 8,
            44,
            36
        )

        actions_y = PADDING + editor_height + ROW_SPACING

        self.scroll.frame = (
            0,
            actions_y,
            self.width,
            self.height - actions_y
        )

        if not self._rows_built:
            self._build_rows()
            self._rows_built = True

        y = PADDING

        for row in self.scroll.subviews:
            row.frame = (
                PADDING,
                y,
                self.width - 2 * PADDING,
                ROW_HEIGHT
            )
            y += ROW_HEIGHT + ROW_SPACING

        self.scroll.content_size = (
            self.width,
            max(y + PADDING, self.scroll.height + 1)
        )

        if not self._loaded_once:
            self.load_clipboard()
            self._loaded_once = True

    def _add_row(
        self,
        title,
        description,
        callback,
        tint=TEXT_COLOR
    ):
        row = ActionRow(
            title,
            description,
            callback,
            tint=tint
        )
        row.set_help_mode(self.root.help_mode)
        self.scroll.add_subview(row)

    def _build_rows(self):
        self._add_row(
            '💾 Save Clipboard',
            'Save the text shown above back to the iOS clipboard.',
            self._save_clipboard
        )

        self._add_row(
            '🔄 Reload Clipboard',
            'Discard edits above and reload the current clipboard.',
            self._reload_clipboard
        )

        self._add_row(
            '🧹 Clean Text',
            'Normalise newlines and remove trailing whitespace.',
            self._clean_text
        )

        self._add_row(
            '📥 Replace Script',
            'Replace the whole open script with the text shown above.',
            self._replace_script,
            tint=WARN_COLOR
        )

        self._add_row(
            '➕ Append to Script',
            'Append the text shown above to the open script.',
            self._append_script
        )

        self._add_row(
            '🗑️ Clear Clipboard',
            'Empty both this editor and the iOS clipboard.',
            self._clear_clipboard,
            tint=DELETE_COLOR
        )

    def set_help_mode(self, enabled):
        for row in self.scroll.subviews:
            if isinstance(row, ActionRow):
                row.set_help_mode(enabled)

    def _dismiss_keyboard(self, sender=None):
        """Dismiss the clipboard editor keyboard without changing its text."""
        self.root.dismiss_keyboard()

    def load_clipboard(self):
        try:
            self.textview.text = clipboard.get() or ''
        except Exception:
            self.textview.text = ''

    def _save_clipboard(self):
        self._dismiss_keyboard()
        clipboard.set(self.textview.text or '')
        hud('Clipboard saved')

    def _reload_clipboard(self):
        self._dismiss_keyboard()
        self.load_clipboard()
        hud('Clipboard reloaded')

    def _clean_text(self):
        self._dismiss_keyboard()
        cleaned = clean_text(self.textview.text or '')
        self.textview.text = cleaned
        clipboard.set(cleaned)
        hud('Text cleaned')

    def _replace_script(self):
        self._dismiss_keyboard()
        text = self.textview.text or ''
        clipboard.set(text)

        if replace_active_text(text):
            hud('Script replaced')

        self.root.close_after()

    def _append_script(self):
        self._dismiss_keyboard()
        text = self.textview.text or ''
        clipboard.set(text)

        if append_to_active_text(text):
            hud('Text appended')

        self.root.close_after()

    def _clear_clipboard(self):
        self._dismiss_keyboard()
        self.textview.text = ''
        clipboard.set('')
        hud('Clipboard cleared')


# ============================================================
# Find / replace page
# ============================================================

class FindReplacePage(ui.View):
    title = 'Replace'

    def __init__(self, root):
        super().__init__()

        self.background_color = BG_COLOR
        self.root = root

        self.scroll = ui.ScrollView(background_color=BG_COLOR)
        self.scroll.shows_vertical_indicator = True

        self._scroll_delegate = KeyboardDismissScrollDelegate(root)
        self.scroll.delegate = self._scroll_delegate

        self.add_subview(self.scroll)

        self.find_label = self._make_label('Find')
        self.find_field = self._make_text_field('Find text')

        self.replace_label = self._make_label('Replace')
        self.replace_field = self._make_text_field('Replace with')

        self.find_clipboard_row = ActionRow(
            '📋 Find from Clipboard',
            'Use the current clipboard text as the search term.',
            self._find_from_clipboard
        )

        self.replace_clipboard_row = ActionRow(
            '📋 Replace from Clipboard',
            'Use the current clipboard text as the replacement text.',
            self._replace_from_clipboard
        )

        self.replace_all_row = ActionRow(
            '🔎 Replace All',
            'Replace every exact match in the open script, then close.',
            self._replace_all,
            tint=WARN_COLOR
        )

        for row in (
            self.find_clipboard_row,
            self.replace_clipboard_row,
            self.replace_all_row
        ):
            row.set_help_mode(self.root.help_mode)

        for view in (
            self.find_label,
            self.find_field,
            self.find_clipboard_row,
            self.replace_label,
            self.replace_field,
            self.replace_clipboard_row,
            self.replace_all_row
        ):
            self.scroll.add_subview(view)

    def _make_label(self, text):
        return ui.Label(
            text=text,
            text_color=MUTED_COLOR,
            font=(FONT_NAME, SMALL_FONT_SIZE),
            alignment=ui.ALIGN_LEFT
        )

    def _make_text_field(self, placeholder):
        field = ui.TextField()

        # Pythonista's native text field can render with a light system fill.
        # Embrace that deliberately: light input, dark text, dark surrounding UI.
        field.background_color = INPUT_BG_COLOR
        field.text_color = INPUT_TEXT_COLOR
        field.tint_color = ACCENT_COLOR
        field.font = (FONT_NAME, FONT_SIZE)
        field.corner_radius = INPUT_RADIUS
        field.border_width = 0
        field.placeholder = placeholder
        field.clear_button_mode = 'while_editing'
        field.action = self._field_finished

        try:
            field.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
            field.autocorrection_type = False
            field.spellchecking_type = False
        except Exception:
            pass

        return field

    def _field_finished(self, sender):
        """Hide the software keyboard when Return is pressed."""
        self.root.dismiss_keyboard()

    def layout(self):
        self.scroll.frame = self.bounds

        width = self.width
        y = PADDING

        self.find_label.frame = (
            PADDING,
            y,
            width - 2 * PADDING,
            22
        )
        y += 28

        self.find_field.frame = (
            PADDING,
            y,
            width - 2 * PADDING,
            INPUT_HEIGHT
        )
        y += INPUT_HEIGHT + ROW_SPACING

        self.find_clipboard_row.frame = (
            PADDING,
            y,
            width - 2 * PADDING,
            ROW_HEIGHT
        )
        y += ROW_HEIGHT + 24

        self.replace_label.frame = (
            PADDING,
            y,
            width - 2 * PADDING,
            22
        )
        y += 28

        self.replace_field.frame = (
            PADDING,
            y,
            width - 2 * PADDING,
            INPUT_HEIGHT
        )
        y += INPUT_HEIGHT + ROW_SPACING

        self.replace_clipboard_row.frame = (
            PADDING,
            y,
            width - 2 * PADDING,
            ROW_HEIGHT
        )
        y += ROW_HEIGHT + 42

        self.replace_all_row.frame = (
            PADDING,
            y,
            width - 2 * PADDING,
            ROW_HEIGHT
        )
        y += ROW_HEIGHT + PADDING

        self.scroll.content_size = (
            width,
            max(y, self.height + 1)
        )

    def set_help_mode(self, enabled):
        self.find_clipboard_row.set_help_mode(enabled)
        self.replace_clipboard_row.set_help_mode(enabled)
        self.replace_all_row.set_help_mode(enabled)

    def _find_from_clipboard(self):
        self.find_field.text = clipboard.get() or ''
        self.root.dismiss_keyboard()
        hud('Find text loaded')

    def _replace_from_clipboard(self):
        self.replace_field.text = clipboard.get() or ''
        self.root.dismiss_keyboard()
        hud('Replacement loaded')

    def _replace_all(self):
        self.root.dismiss_keyboard()

        find_text = self.find_field.text or ''
        replacement = self.replace_field.text or ''

        if not find_text:
            hud('Enter text to find', 'error', 0.9)
            return

        text = active_text()
        count = text.count(find_text)

        if not count:
            hud('No matches', 'error', 0.9)
            return

        if replace_active_text(text.replace(find_text, replacement)):
            hud('Replaced %d' % count)

        self.root.close_after()


# ============================================================
# Root navigation
# ============================================================

class KeyboardDismissScrollDelegate(object):
    """
    Hide the keyboard whenever a non-editor scrolling surface is manipulated.

    The clipboard TextView deliberately does not use this delegate, so users
    can still scroll long clipboard contents while keeping the keyboard open.
    """

    def __init__(self, root):
        self.root = root

    def scrollview_will_begin_dragging(self, scrollview):
        self.root.dismiss_keyboard()

    def scrollview_did_scroll(self, scrollview):
        self.root.dismiss_keyboard()


class PagerDelegate(object):
    """Keep tab navigation in sync and aggressively hide keyboards on swipes."""

    def __init__(self, root):
        self.root = root

    def scrollview_will_begin_dragging(self, scrollview):
        self.root.dismiss_keyboard()

    def scrollview_did_scroll(self, scrollview):
        self.root.dismiss_keyboard()
        self.root.sync_page_from_offset()


class RootApp(ui.View):
    PAGE_TITLES = ('Quick', 'Clipboard', 'Replace')

    def __init__(self):
        super().__init__()

        self.background_color = BG_COLOR
        self.help_mode = False
        self.current_page = 0

        self.close_button = ui.Button(
            title='✕',
            font=(FONT_NAME, 22),
            tint_color=TEXT_COLOR
        )
        self.close_button.action = self._close_tapped
        self.add_subview(self.close_button)

        self.title_label = ui.Label(
            text=self.PAGE_TITLES[0],
            text_color=TEXT_COLOR,
            font=(FONT_NAME, 16),
            alignment=ui.ALIGN_CENTER
        )
        self.add_subview(self.title_label)

        self.help_button = ui.Button(
            title='?',
            font=(FONT_NAME, 19),
            tint_color=MUTED_COLOR
        )
        self.help_button.action = self._toggle_help
        self.add_subview(self.help_button)

        self.pager = ui.ScrollView(background_color=BG_COLOR)
        self.pager.paging_enabled = True
        self.pager.shows_horizontal_indicator = False

        self._pager_delegate = PagerDelegate(self)
        self.pager.delegate = self._pager_delegate

        self.add_subview(self.pager)

        self.quick_page = QuickPage(self)
        self.clipboard_page = ClipboardPage(self)
        self.replace_page = FindReplacePage(self)

        self.pages = [
            self.quick_page,
            self.clipboard_page,
            self.replace_page
        ]

        for page in self.pages:
            self.pager.add_subview(page)

        self.tab_bar = ui.View(background_color=CARD_2_COLOR)
        self.add_subview(self.tab_bar)

        self.tab_buttons = []

        for index, title in enumerate(self.PAGE_TITLES):
            button = ui.Button(
                title=title,
                font=(FONT_NAME, 14),
                tint_color=MUTED_COLOR
            )
            button.action = self._tab_action(index)
            self.tab_bar.add_subview(button)
            self.tab_buttons.append(button)

        self._update_navigation(0)

    def layout(self):
        width = self.width
        height = self.height

        self.close_button.frame = (
            PADDING,
            37,
            44,
            40
        )

        self.help_button.frame = (
            width - PADDING - 44,
            37,
            44,
            40
        )

        self.title_label.frame = (
            64,
            39,
            width - 128,
            36
        )

        pager_height = max(
            1,
            height - HEADER_HEIGHT - TAB_BAR_HEIGHT
        )

        self.pager.frame = (
            0,
            HEADER_HEIGHT,
            width,
            pager_height
        )

        for index, page in enumerate(self.pages):
            page.frame = (
                index * width,
                0,
                width,
                pager_height
            )

        self.pager.content_size = (
            width * len(self.pages),
            pager_height
        )

        self.tab_bar.frame = (
            0,
            height - TAB_BAR_HEIGHT,
            width,
            TAB_BAR_HEIGHT
        )

        tab_width = width / float(len(self.tab_buttons))

        for index, button in enumerate(self.tab_buttons):
            button.frame = (
                index * tab_width + 5,
                7,
                tab_width - 10,
                48
            )
            button.corner_radius = 10

        # Preserve the selected page after rotation/layout changes.
        self.pager.content_offset = (
            self.current_page * width,
            0
        )

        for page in self.pages:
            try:
                page.layout()
            except Exception:
                pass

    def _tab_action(self, index):
        def action(sender):
            self.go_to_page(index)
        return action

    def dismiss_keyboard(self):
        """Dismiss whichever Pythonista text control currently owns the keyboard."""
        if dismiss_system_keyboard():
            return True

        # Lightweight fallback for environments where objc_util is unavailable.
        for control in (
            getattr(self.clipboard_page, 'textview', None),
            getattr(self.replace_page, 'find_field', None),
            getattr(self.replace_page, 'replace_field', None),
        ):
            if control is None:
                continue

            try:
                control.end_editing()
                return True
            except Exception:
                pass

        return False

    def _close_tapped(self, sender):
        self.dismiss_keyboard()
        self.close()

    def close_after(self, delay=0.05):
        ui.delay(self.close, delay)

    def _toggle_help(self, sender):
        self.dismiss_keyboard()

        self.help_mode = not self.help_mode

        for page in self.pages:
            try:
                page.set_help_mode(self.help_mode)
            except Exception:
                pass

        self.help_button.tint_color = (
            ACCENT_COLOR if self.help_mode else MUTED_COLOR
        )
        self.help_button.background_color = (
            HELP_BUTTON_COLOR if self.help_mode else BG_COLOR
        )
        self.help_button.corner_radius = 10

    def go_to_page(self, index):
        index = max(0, min(index, len(self.pages) - 1))

        self.dismiss_keyboard()

        width = self.pager.width or self.width

        self.pager.content_offset = (
            width * index,
            0
        )

        self._update_navigation(index)

        if index == 1:
            self.clipboard_page.load_clipboard()

    def sync_page_from_offset(self):
        width = self.pager.width

        if not width:
            return

        offset_x = self.pager.content_offset[0]
        index = int(round(offset_x / float(width)))
        index = max(0, min(index, len(self.pages) - 1))

        if index != self.current_page:
            self.dismiss_keyboard()
            self._update_navigation(index)

            if index == 1:
                self.clipboard_page.load_clipboard()

    def _update_navigation(self, index):
        self.current_page = index
        self.title_label.text = self.PAGE_TITLES[index]

        for button_index, button in enumerate(self.tab_buttons):
            selected = button_index == index

            button.tint_color = (
                ACCENT_COLOR if selected else MUTED_COLOR
            )
            button.background_color = (
                TAB_ACTIVE_COLOR if selected else CARD_2_COLOR
            )


def main():
    app = RootApp()
    app.present('fullscreen', hide_title_bar=True)


if __name__ == '__main__':
    main()
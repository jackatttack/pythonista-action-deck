# Pythonista Action Deck

A fast, touch-friendly utility panel for [Pythonista](https://omz-software.com/pythonista/) on iPhone and iPad.

Action Deck is designed to live in Pythonista's **editor action / wrench menu**. Open the script you are working on, summon Action Deck from the wrench menu, and use it to perform common editor and clipboard jobs without leaving your workflow.

> **Important:** Action Deck is not really a standalone app.
>
> It operates on the script that is currently open in Pythonista's editor. If you simply open `action_deck.py` and run it normally, Action Deck will see **itself** as the active script. Add it to the wrench menu and launch it while the script you actually want to work with is open.

## What it does

### Quick

Fast actions for the currently open Pythonista script:

- Copy the whole script
- Copy its filesystem path
- Copy a `pythonista3://` URL that **runs** it
- Copy a `pythonista3://` URL that **opens** it
- Tune the script's top-level constants (see [Tune Constants](#tune-constants))
- Replace the script with clipboard contents
- Duplicate the script beside the original
- Clear the script, with confirmation

### Clipboard

A proper clipboard editor inside Action Deck:

- View and edit clipboard text
- Save or reload the clipboard
- Clean whitespace and line endings
- Replace the active script with the edited text
- Append edited text to the active script
- Clear the clipboard

The keyboard can be dismissed explicitly and also gets out of the way when navigating or scrolling elsewhere in the app.

### Find / Replace

Simple whole-script find and replace, including buttons for loading either field directly from the clipboard.

### Tune Constants

Many Pythonista scripts keep their settings as top-level constants:

    ACCENT_COLOR = '#6596FF'
    TILE_SIZE = 64  # range: 16-128
    SPEED = 0.25
    DEBUG = False

**🎛️ Tune Constants** on the Quick page opens a sheet listing every top-level `UPPER_CASE` name set to a plain value in the open script, grouped under its `# ====` banner comments:

- **numbers** get a slider and a typed field
- **True / False** gets a switch
- **hex colours** get a swatch that opens hue, saturation and brightness sliders
- **text** and other literals (tuples, lists, dicts) get an editable field

Each change is written straight into the editor, keeping your quote style, hex case and decimal places, and can be undone there. Anything computed, such as `ROOT = os.path.expanduser('~')`, is left alone.

A slider runs from 0 to twice the current value by default. Add a trailing `# range: low-high` comment to set the range yourself.

## Navigation

Action Deck supports both:

- **bottom tabs**
- **horizontal swiping**

Tap the **?** button at the top to switch every action from its short name to a plain-English explanation of what it does.

## Install

### Quick installer

Create a new Python file in Pythonista, paste this in and run it once:

    from urllib.request import urlopen

    url = (
        'https://raw.githubusercontent.com/'
        'jackatttack/pythonista-action-deck/main/install.py'
    )
    source = urlopen(url).read()
    exec(compile(source, 'install.py', 'exec'))

The installer creates:

    ~/Documents/Pythonista Action Deck/action_deck.py

and opens the installed script when it is finished.

You can also read [`install.py`](install.py) before running it.

**One manual step remains:** add `action_deck.py` to Pythonista's wrench / action menu. Action Deck is designed to act on whichever editor script is open when you launch it.

## Add it to Pythonista's wrench menu

After installing:

1. Open Pythonista's **wrench / action menu**.
2. Choose **Edit**.
3. Add a new script action.
4. Select:

       Pythonista Action Deck/action_deck.py

5. Finish editing the action menu.

The exact wording can vary slightly between Pythonista versions, but the goal is simply to make `action_deck.py` available as an editor action.

## Using it

Once it is in the wrench menu:

1. Open the Python script you want to work with.
2. Tap the wrench icon.
3. Launch **Action Deck**.
4. Choose an action.
5. Most quick actions automatically close the deck when complete.

That distinction matters: **the script you have open before launching Action Deck is the script Action Deck works on.**

## Pythonista URLs

Action Deck can generate links such as:

    pythonista3://projects/games/example.py?action=run

or:

    pythonista3://projects/games/example.py?action=open

These are useful in Notes, Shortcuts, other scripts, launchers, documentation, and anywhere else that can open a URL.

## Design

Action Deck deliberately stays lightweight:

- one main Python file
- no `.pyui`
- no external packages
- no background services
- no project-specific integrations
- large touch targets
- dark interface designed for iPhone and iPad
- Pythonista's built-in `ui`, `editor`, `clipboard`, `console`, and `objc_util` modules, plus the Python standard library

## Safety

A few actions deliberately modify the whole active editor buffer.

Actions such as **Replace with Clipboard** are visually highlighted, while **Clear Script** asks for confirmation.

For anything important, saving your work before destructive editor operations is still a good habit.

## Requirements

- Pythonista 3
- iPhone or iPad
- iOS / iPadOS

This project is specifically built around Pythonista APIs and is not intended as a normal desktop Python application.

## License

MIT. See [LICENSE](LICENSE).
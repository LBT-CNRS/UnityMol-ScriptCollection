# remote-console.py
# UnityMol Development Script
# (c) 2025 by Marc BAADEN
# MIT license

# A demo python script to implement an external console for UnityMol
# using the ZMQ server connection

__version__ = "0.1.0"

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout

# from rich import print
# from rich.markdown import Markdown
from rich.console import Console
import re
import sys

import zmq
import json

# AutoSuggest implementation
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

# UnityMol ZMQ setup
# Update the ZMQ connection settings
import unitymol_zmq

# Initialize UnityMolZMQ and connect once
if unitymol_zmq.unitymol is None:
    print("\nDebug: Attempting to establish connection to UnityMol ZMQ server")
    unitymol_zmq.unitymol = unitymol_zmq.UnityMolZMQ()
    unitymol_zmq.unitymol.connect()

# History
history = InMemoryHistory()

# Keybindings
kb = KeyBindings()

# Rich console setup
console = Console(file=sys.__stdout__, markup=True)

exit_requested = False

def html_to_rich(text):
    """Convert HTML-like tags to Rich markup, assuming square brackets were handled"""
    if not text:
        return ""
    
    # Convert to string and escape square brackets first
    text = str(text)

    # Simple replacements: <b> → [bold], </b> → [/bold], etc.
    text = re.sub(r'<b>', '[bold]', text)
    text = re.sub(r'</b>', '[/bold]', text)
    text = re.sub(r'<i>', '[italic]', text)
    text = re.sub(r'</i>', '[/italic]', text)
    text = re.sub(r'<u>', '[underline]', text)
    text = re.sub(r'</u>', '[/underline]', text)
    
    return text

def replace_brackets(text):
    # Replace [ with fullwidth ［ (U+FF3B)
    # Replace ] with fullwidth ］ (U+FF3D)
    text = text.replace('[', '［')
    text = text.replace(']', '］')
    return text

@kb.add('c-c', 'c-c')  # Ctrl-C Ctrl-C to send
def _(event):
    buffer = event.app.current_buffer
    text = buffer.text.strip()
    if text:
        # Save to history manually
        history.append_string(text)

        # Send over ZMQ
        data = unitymol_zmq.unitymol.send_command(text)
        # Now you can access the dictionary keys
        success = data.get("success", "false")  # Defaults to "false" if key is not found
        result = data.get("result", "No result")
        stdout = data.get("stdout", "No output")

        if success:
            console.print("\n[green]--- Reply from server ---[/green]")
            console.print(html_to_rich(replace_brackets(result)))
            console.print(html_to_rich(replace_brackets(stdout)))
            console.print("[green]--- End of reply ---[/green]")
            buffer.reset()  # Clear buffer after sending
        else:
            console.print("\n[red]--- Server replied with error !! ---[/red]\n")    
    else:
        console.print("\n[yellow][Empty input, nothing sent][/yellow]")

@kb.add('c-c', 'c-q')
def _(event):
    global exit_requested
    console.print("\n[red][Quit requested]")
    exit_requested = True
    event.app.exit()

@kb.add('c-l')
def _(event):
    console.clear()
    
# Create prompt session
session = PromptSession(
    "> ",
    multiline=True,
    key_bindings=kb,
    history=history,
    auto_suggest=AutoSuggestFromHistory(),
)

print("Multiline ZMQ editor. Prints out command result, stdout and one blank line.")
print("Use C-c C-c to send, C-c C-q to quit.")
print("C-a / C-e / M-d etc. for Emacs-style editing. Arrows or M-p / M-n for history.")
#print("Tab to cycle through suggestions.")

# REPL loop
while not exit_requested:
    with patch_stdout():
        try:
            session.prompt()
        except (EOFError, KeyboardInterrupt):
            console.print("[red]\n[Interrupted]")
            break

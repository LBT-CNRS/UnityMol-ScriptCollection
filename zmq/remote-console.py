# A demo python script to implement an external console for UnityMol
# using the ZMQ server connection

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout

import zmq
import json

# ZMQ setup
socket = zmq.Context.instance().socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

# History
history = InMemoryHistory()

# Keybindings
kb = KeyBindings()

exit_requested = False

@kb.add('c-c', 'c-c')  # Ctrl-C Ctrl-C to send
def _(event):
    buffer = event.app.current_buffer
    text = buffer.text.strip()
    if text:
        # Save to history manually
        history.append_string(text)

        # Send over ZMQ
        socket.send_string(text)
        reply = socket.recv().decode()
        # Deserialize the JSON string to a Python dictionary
        data = json.loads(reply)
        # Now you can access the dictionary keys
        success = data.get("success", "false")  # Defaults to "false" if key is not found
        result = data.get("result", "No result")
        stdout = data.get("stdout", "No output")
        
        if (success):
            print("\n--- Reply from server ---\n" + result + "\n" + stdout + "\n--- End of reply ---\n")
            buffer.reset()  # Clear buffer after sending
        else:
            print("\n--- Server replied with error !! ---\n")
    else:
        print("\n[Empty input, nothing sent]")

@kb.add('c-c', 'c-q')
def _(event):
    global exit_requested
    print("\n[Quit requested]")
    exit_requested = True
    event.app.exit()

# Create prompt session
session = PromptSession(
    "> ",
    multiline=True,
    key_bindings=kb,
    history=history
)

print("Multiline ZMQ editor. Use C-c C-c to send, C-c C-q to quit.")
print("C-a / C-e / M-d etc. for Emacs-style editing. Arrows or M-p / M-n for history.")

# REPL loop
while not exit_requested:
    with patch_stdout():
        try:
            session.prompt()
        except (EOFError, KeyboardInterrupt):
            print("\n[Interrupted]")
            break

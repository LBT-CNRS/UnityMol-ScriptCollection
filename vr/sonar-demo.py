import UnityEngine
from UnityEngine import Vector3
import time

# --- Global state ---
sound_position = Vector3(0.0, 0.0, 0.0)
sound_loop_active = False
uiref = "CanvasMainUI/Selection Scroll View/Viewport/Content/"

def button_ref(button):
    global uiref
    return GameObject.Find(uiref+button).GetComponent("Button")
    
# --- Coroutine to play sound every 2 seconds ---
def sound_loop():
    global sound_loop_active
    sound_loop_active = True
    while sound_loop_active:
        playSoundAtPosition(sound_position)
        yield APIPython.pythonConsole.waitSeconds(1.9)

# Check if the Tour menu is already open, if not open it
if(GameObject.Find(uiref+"TourLabel/PanelLayer/Expand").activeSelf):
    b=button_ref("TourLabel/PanelLayer")
    b.onClick.Invoke()

def go():
    # --- Activate sound ---
    def activate_sound_loop():
        global sound_loop_active
        global sound_position
        if sound_loop_active:
            print("WARNING:: Sound loop already active.")
        else:
            print("NOTE:: Starting sound loop every 2 seconds at ", sound_position[0], sound_position[1], sound_position[2])
            APIPython.pythonConsole.doCoroutine(sound_loop())

    # --- Stop sound ---
    def stop_sound():
        global sound_loop_active
        sound_loop_active = False
        print("NOTE:: Sound loop stopped.")

    # Get the reference to the "Start Tour" button
    b=button_ref("TourButtons/TourStart/Button Layer")
    if b:
        b.onClick.AddListener(activate_sound_loop)
    else:
        print("Start Tour Button component not found! Maybe the Tour menu was not opened?")

    b=button_ref("TourButtons/TourPrev/Button Layer")
    if b:
        b.onClick.AddListener(stop_sound)
    else:
        print("TourPrev Button component not found! Maybe the Tour menu was not opened?")

    b=button_ref("TourButtons/TourNext/Button Layer")
    if b:
        b.onClick.AddListener(stop_sound)
    else:
        print("TourNext Button component not found! Maybe the Tour menu was not opened?")

# All has been set up, let's go!
go()

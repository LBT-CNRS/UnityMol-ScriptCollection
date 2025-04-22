from UnityEngine import Vector3, GameObject
import System

# --- Global state ---
sound_position = Vector3(0.0, 0.0, 0.0)
sound_loop_active = False
rnd = System.Random()
uiref = "CanvasMainUI/Selection Scroll View/Viewport/Content/"

def button_ref(path):
    return GameObject.Find(uiref + path).GetComponent("Button")

def random_res_pos(s):
    nres = s.currentModel.GetChains()[0].residues.Count
    resid = rnd.Next(1, nres + 1)
    sel=select("resid {} and name CA".format(resid))
    return sel.atoms[0].position if sel.atoms else None

def print_position(label, pos):
    print("{} {:.3f}, {:.3f}, {:.3f}".format(label, pos[0], pos[1], pos[2]))

# --- Coroutine to play sound every 2 seconds ---
def sound_loop():
    global sound_loop_active
    sound_loop_active = True
    while sound_loop_active:
        playSoundAtPosition(sound_position)
        yield APIPython.pythonConsole.waitSeconds(1.9)

# Check if the Tour menu is already open, if not open it
if GameObject.Find(uiref + "TourLabel/PanelLayer/Expand").activeSelf:
    button_ref("TourLabel/PanelLayer").onClick.Invoke()

def go():
    # --- Activate sound ---
    def activate_sound_loop():
        global sound_loop_active, sound_position
        if sound_loop_active:
            print("WARNING:: Sound loop already active.")
        else:
            print_position("NOTE:: Starting sound loop every 2 seconds at", sound_position)
            APIPython.pythonConsole.doCoroutine(sound_loop())

    # --- Stop sound ---
    def stop_sound():
        global sound_loop_active
        sound_loop_active = False
        print("NOTE:: Sound loop stopped.")

    # --- Set sound position randomly ---
    def random_sound_position():
        global sound_position
        sound_position = random_res_pos(last())
        print_position("NOTE:: Sound position set to:", sound_position)

    buttons = {
        "TourButtons/TourStart/Button Layer": activate_sound_loop,
        "TourButtons/TourPrev/Button Layer": stop_sound,
        "TourButtons/TourNext/Button Layer": random_sound_position,
    }

    for path in buttons:
        callback = buttons[path]
        b = button_ref(path)
        if b:
            b.onClick.AddListener(callback)
        else:
            print("Button '{}' not found! Maybe the Tour menu was not opened?".format(path))

    # # Get the reference to the "Start Tour" button
    # b=button_ref("TourButtons/TourStart/Button Layer")
    # if b:
    #     b.onClick.AddListener(activate_sound_loop)
    # else:
    #     print("Start Tour Button component not found! Maybe the Tour menu was not opened?")

    # b=button_ref("TourButtons/TourPrev/Button Layer")
    # if b:
    #     b.onClick.AddListener(stop_sound)
    # else:
    #     print("TourPrev Button component not found! Maybe the Tour menu was not opened?")

    # b=button_ref("TourButtons/TourNext/Button Layer")
    # if b:
    #     b.onClick.AddListener(random_sound_position)
    # else:
    #     print("TourNext Button component not found! Maybe the Tour menu was not opened?")

# Load a PDB to play with
fetch("1crn")

# Initialize a random position for the first sound
sound_position = random_res_pos(last())

# All has been set up, let's go!
go()

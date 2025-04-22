from UnityEngine import Vector3, GameObject
import System

# --- Global state ---
sound_loop_active = False
rnd = System.Random()
uiref = "CanvasMainUI/Selection Scroll View/Viewport/Content/"

# --- Utility functions ---
def random_atom_pos(sel):
    natom = sel.atoms.Count
    if natom == 0:
        return None
    atid = rnd.Next(0, natom)
    return sel.atoms[atid].position

def myform(label, pos):
    return "{} {:.3f}, {:.3f}, {:.3f}".format(label, pos[0], pos[1], pos[2])

def button_ref(path):
    return GameObject.Find(uiref + path).GetComponent("Button")

# --- Coroutine to play sound every 2 seconds ---
def sound_loop():
    global sound_loop_active
    sound_loop_active = True
    while sound_loop_active:
        playSoundAtPosition(sound_position)
        yield APIPython.pythonConsole.waitSeconds(1.9)

# --- Function to set up callbacks ---
def go():
    # --- Activate sound ---
    def activate_sound_loop():
        global sound_loop_active, sound_position
        if sound_loop_active:
            Debug.Log("WARNING:: Sound loop already active.")
        else:
            Debug.Log(myform("NOTE:: Starting sound loop every 2 seconds at", sound_position))
            APIPython.pythonConsole.doCoroutine(sound_loop())

    # --- Stop sound ---
    def stop_sound():
        global sound_loop_active
        sound_loop_active = False
        Debug.Log("NOTE:: Sound loop stopped.")

    # --- Set sound position randomly ---
    def random_sound_position():
        global sound_position
        sound_position = random_atom_pos(sel_all)
        Debug.Log(myform("NOTE:: Sound position set to:", sound_position))

    buttons = {
        "TourButtons/TourStart/Button Layer": activate_sound_loop,
        "TourButtons/TourPrev/Button Layer": stop_sound,
        "TourButtons/TourNext/Button Layer": random_sound_position,
    }

    for path, callback in buttons.items():
        b = button_ref(path)
        if b:
            b.onClick.AddListener(callback)
        else:
            print("Button '{}' not found! Maybe the Tour menu was not opened?".format(path))

# Check if the Tour menu is already open, if not open it
if GameObject.Find(uiref + "TourLabel/PanelLayer/Expand").activeSelf:
    button_ref("TourLabel/PanelLayer").onClick.Invoke()

# Load a PDB and init
fetch("3eam")
sel_all = select("all")
sound_position = random_atom_pos(sel_all)
go()

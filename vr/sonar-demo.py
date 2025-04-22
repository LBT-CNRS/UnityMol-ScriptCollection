from UnityEngine import Vector3, GameObject
import System

# --- Global state ---
sound_position = Vector3(0.0, 0.0, 0.0)
sound_loop_active = False
rnd = System.Random()
uiref = "CanvasMainUI/Selection Scroll View/Viewport/Content/"

def button_ref(path):
    return GameObject.Find(uiref + path).GetComponent("Button")

def random_res_pos(sel):
    natom = sel.atoms.Count
    atid = rnd.Next(1, natom + 1)
    return sel.atoms[atid].position if sel.atoms else None

def myform(label, pos):
    return "{} {:.3f}, {:.3f}, {:.3f}".format(label, pos[0], pos[1], pos[2])

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
        sound_position = random_res_pos(a)
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

# Load a PDB and init
fetch("3eam")
a=select("all")
sound_position = random_res_pos(a)
go()

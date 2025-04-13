# UnityMol Development Script
# (c) 2025 by Marc BAADEN
# MIT license

import unitymol_zmq

if unitymol_zmq.unitymol is None:
    unitymol_zmq.unitymol = unitymol_zmq.UnityMolZMQ()
    unitymol_zmq.unitymol.connect()

print(unitymol_zmq.unitymol.send_command_clean("ls()"))


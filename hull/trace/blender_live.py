# One Blender window for the whole session (asked: reopen in the same window, not a new one each time): started once with
# this script, it watches a request file; writing a .blend path into it makes this window open that file (UI kept), so a
# finished step shows up where Adrian is already looking. Start: env -u WAYLAND_DISPLAY blender -p 0 0 4096 2560 <file>
# --python blender_live.py ; open: echo <file.blend> > .temp/trace/blender_live.req
import bpy, os
from bpy.app.handlers import persistent
REQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_live.req")
seen = [os.path.getmtime(REQ) if os.path.exists(REQ) else 0.0]
def watch():
    try:
        t = os.path.getmtime(REQ)
        if t > seen[0]:
            seen[0] = t; fn = open(REQ).read().strip()
            if fn and os.path.exists(fn): bpy.ops.wm.open_mainfile(filepath=fn, load_ui=False); print("LIVE deschis", fn)
    except Exception as e: print("LIVE", e)
    return 1.0
@persistent
def again(_):
    if not bpy.app.timers.is_registered(watch): bpy.app.timers.register(watch, first_interval=1.0, persistent=True)
bpy.app.handlers.load_post.append(again); bpy.app.timers.register(watch, first_interval=1.0, persistent=True)

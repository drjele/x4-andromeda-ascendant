# One Blender window driven from outside: every second, run and remove the command file if present.
import bpy, os, traceback
CMD = "/tmp/claude-1000/blender_cmd.py"
LOG = "/tmp/claude-1000/blender_cmd.log"
def poll():
    if os.path.exists(CMD):
        code = open(CMD).read(); os.remove(CMD)
        try:
            exec(compile(code, CMD, "exec"), {"bpy": bpy})
            open(LOG, "a").write("ok\n")
        except Exception:
            open(LOG, "a").write(traceback.format_exc())
    return 1.0
bpy.app.timers.register(poll, first_interval=1.0, persistent=True)

import os
from psychopy import visual, event, core
import ctypes
import helper_functions as hf

print('Reminder: Press Q to quit.')
duration = 7  # Duration of the fixation cross in minutes
send_triggers = True  # Set to True to send triggers

# WINDOW
win = visual.Window(
    size=[1512, 982],  # Set to actual screen size
    fullscr=True,  # Full-screen mode
    screen=1,
    allowGUI=True,
    color='black',
    blendMode='avg',
    useFBO=True,  # Frame Buffer Object for rendering (good for complex stimuli)
    units='pix'
)

# MOUSE
win.setMouseVisible(False)
if os.name == 'nt':  # Windows-specific: hide cursor
    ctypes.windll.user32.ShowCursor(False)

# EEG TRIGGERS
triggers = dict(
    start=1,
    end=2
)
EEG_config = hf.EEGConfig(triggers, send_triggers)

# FIXATION CROSS
fixation = visual.TextStim(
    win=win,
    text='+',
    height=100,
    pos=[0, 0],
    color='white',
    font='Arial'
)

# Draw fixation and send EEG trigger
fixation.draw()
win.flip()
EEG_config.send_trigger(EEG_config.triggers['start'])

# Wait for 5 seconds, checking for exit keypress continuously
start_time = core.getTime()
while core.getTime() - start_time < (60 * duration):
    # Check if the user presses 'Q' to quit
    hf.exit_q(win)  # This should check for exit condition during fixation
    # Allow other events like keyboard input
    event.clearEvents()
    core.wait(0.1)  # Small wait to prevent max CPU usage during the loop

# Send end trigger
EEG_config.send_trigger(EEG_config.triggers['end'])

# End
instructions_txt = visual.TextStim(
    win=win,
    text='Please let the experimenter know that you are done!',
    height=40,
    pos=[0, 10],
    color='white',
    font='Arial'
)
instructions_txt.draw()
win.flip()
core.wait(5)
event.clearEvents()
win.close()
core.quit()

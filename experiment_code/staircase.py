"""
script for staircasing the perceptual stimulus
do this on the structural scan day
only calibrate once to keep the objective stimulus the same across stimulation sessions, rather than re-calibrating each time
the calibration process alternates between calibrating motion coherence vs choice boundary

Maja Friedemann 2024
"""
from psychopy import visual, core, event, monitors

# Create a monitor profile (ensure this matches the name used in Monitor Center)
mon = monitors.Monitor('maja_dell_1')  # replace 'myMonitor' with your monitor name

# Create a window in degrees using the monitor profile
win = visual.Window(
    size=(800, 600), units="pix", fullscr=False, color=(0, 0, 0), colorSpace='rgb', monitor=mon
)

# Create a fixation cross
fixation = visual.ShapeStim(
    win=win, vertices='cross', size=(1, 1), lineColor='white', fillColor='white'
)

# Create a circle stimulus
circle = visual.Circle(
    win=win, radius=1, edges=128, lineColor='red', fillColor='red'
)

# Draw fixation cross and flip window
fixation.draw()
win.flip()

# Wait for 1 second
core.wait(1.0)

# Draw circle at a location (5, 5) degrees
circle.pos = (5, 5)
circle.draw()
win.flip()

# Wait for 2 seconds or until a key is pressed
event.waitKeys(maxWait=2)

# Close the window
win.close()
core.quit()

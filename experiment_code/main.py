###################################
# IMPORT PACKAGES
###################################
import csv
import json
import numpy as np
import os
import random
from datetime import datetime
import time
from psychopy import gui, visual, core, data, event
import helper_functions as hf
import ctypes  # for hiding the mouse cursor on Windows

print('Reminder: Press Q to quit.')

###################################
# SESSION INFO
###################################
# PARTICIPANT INFO POP-UP
expName = 'confidence-pgACC-TUS'
curecID = 'R88533/RE002'
expInfo = {'participant nr': '999',
           'eeg (y/n)': 'n',
           'session nr': '1',
           'age': '',
           'gender (f/m/o)': '',
           }
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False,
                      title=expName)
if not dlg.OK:
    core.quit()

# TASK VARIABLES
gv = dict(
    n_trials=50,  # number of trials
    dot_display_time=1.0,  # duration of dot display, 1 second
    inter_trial_interval=[0.5, 1.0],  # duration of inter-trial interval, uniform distribution, 0.5-1 second
    response_keys=['d', 'e'],  # keys for CW and CCW responses
    low_coherence=0.2,  # low coherence
    high_coherence=0.4,  # high coherence
    low_distance=10,  # low distance
    high_distance=30,  # high distance
)

###################################
# DATA SAVING
###################################
# variables in info will be saved as participant data
info = dict(
    expName=expName,
    curec_ID=curecID,
    session_nr=expInfo['session nr'],
    date=data.getDateStr(),
    start_time=None,
    end_time=None,

    participant=expInfo['participant nr'],
    age=expInfo['age'],
    gender=expInfo['gender (f/m/o)'],

    block_count=0,  # block counter
    trial_count=0,  # trial counter

)

# start a csv file for saving the participant data
log_vars = list(info.keys())
if not os.path.exists('data'):
    os.mkdir('data')
filename = os.path.join('data', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()

############################################
# SET UP WINDOW, MOUSE, EEG TRIGGERS, CLOCK
############################################
# WINDOW
win = visual.Window(
    size=[1512, 982],  # set correct monitor size
    fullscr=True,  # full-screen mode
    screen=1,  # adjust if using multiple monitors
    allowGUI=False,
    color='black',
    blendMode='avg',
    useFBO=True,  # Frame Buffer Object for rendering (good for complex stimuli)
    units='pix',
    # units in pixels (fine for this task but for more complex (e.g. dot motion) stimuli, we probably need visual degrees
    allowStencil=True,
)

# MOUSE
win.setMouseVisible(False)
mouse = event.Mouse(visible=False, win=win)
mouse.setVisible(False)
# Explicitly hide the cursor on Windows
if os.name == 'nt':  # Check if the OS is Windows
    ctypes.windll.user32.ShowCursor(False)

# EEG TRIGGERS
triggers = dict(
    experiment_start=1,
    experiment_end=20
)
# Create an EEGConfig object
send_triggers = expInfo['eeg (y/n)'].lower() == 'y'
EEG_config = hf.EEGConfig(triggers, send_triggers)

# CLOCK
clock = core.Clock()

###################################
# CREATE STIMULI
###################################
green_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -270), fillColor='green')
button_txt = visual.TextStim(win=win, text='NEXT', height=25, pos=green_button.pos, color='black', bold=True,
                             font='Monospace')
big_txt = visual.TextStim(win=win, text='Welcome!', height=90, pos=[0, 50], color='white', wrapWidth=800,
                          font='Monospace')
instructions_txt = visual.TextStim(win=win, text="\n\n\n\n\n\n Press SPACE to start.", height=40, pos=[0, 80], wrapWidth=1100, color='white',
                                   font='Monospace')
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 300], wrapWidth=1200,
                                       color='white', font='Monospace')
dot_params = {  # parameters for dot-patch
    'units': 'pix',
    'nDots': 150,
    'dotSize': 8,
    'speed': 5,
    'fieldSize': [400, 400],
    'fieldShape': 'circle',
    'dotLife': -1,  # number of frames each dot lives for (-1=infinite)
    'signalDots': 'same',  # if ‘same’ then the signal and noise dots are constant. If ‘different’ then the choice of which is signal and which is noise gets randomised on each frame.
    'noiseDots': 'walk'  # ‘position’ = noise dots take a random position every frame; ‘direction’ = noise dots follow a random, but constant direction; ‘walk’ = noise dots vary their direction every frame, but keep a constant speed.
}
fixation = visual.TextStim(win, text='+', height=50, color='white')
no_dot_zone = visual.Circle(win, radius=18, edges=100, fillColor='black')  # black circle around fixation cross
dot_outline = visual.Circle(win, radius=dot_params['fieldSize'][0] / 2, edges=100, lineColor='white', lineWidth=3, fillColor=None)

###################################
# INSTRUCTIONS
###################################
# WELCOME
big_txt.draw()
instructions_txt.draw()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

# TASK REMINDER
instructions_txt.text = ("Now you are ready for the confidence task. \n\n As you'll remember, you will see a cloud of dots moving "
                         "in some direction. Following this, a reference direction will be indicated and your task is to decide "
                         "whether the net direction of motion was towards the BLUE or the ORANGE side of the reference. "
                         "To make a choice, press the BLUE or the ORANGE button on the keyboard. \n\n"
                         "Press SPACE to continue.")
instructions_txt.draw()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

# CONFIDENCE REMINDER
instructions_txt.text = ("On some trials, you will be asked to rate your confidence in your decision on a scale from 50% to 100%. \n\n"
                         "The slider-marker will start out in a random position. Use the left and right arrow keys to move the slider and press SPACE to confirm your response. \n\n"
                         "To maximise your bonus, you must make as many correct decisions as possible and estimate your confidence as accurately as possible. \n\n"
                         "Press SPACE to begin.")
instructions_txt.draw()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()


###################################
# TASK
###################################
EEG_config.send_trigger(EEG_config.triggers['experiment_start'])
start_time = datetime.now()
info['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")

for trial in range(gv['n_trials']):
    # Set the direction, coherence, and reference direction for the trial
    direction = round(np.random.uniform(1, 360), 2)  # randomly choose motion direction

    if np.random.choice([True, False]):  # randomly choose low or high coherence
        coherence = gv['high_coherence']  # this needs to be calibrated to the participant
    else:
        coherence = gv['low_coherence']

    if np.random.choice([True, False]):  # randomly choose low or high distance
        distance = gv['high_distance']  # this needs to be calibrated to the participant
    else:
        distance = gv['low_distance']

    if np.random.choice([True, False]):  # randomly choose CW or CCW
        reference_direction = 'CW'
        reference = (direction + distance) % 360
    else:
        reference_direction = 'CCW'
        reference = (direction - distance) % 360

    print(f"Trial {trial}: direction={direction}, coherence={coherence}, distance={distance}, reference={reference}")

    # Show fixation cross
    stimuli = [dot_outline, fixation]
    delay = np.random.uniform(gv['inter_trial_interval'][0], gv['inter_trial_interval'][1])
    hf.draw_all_stimuli(win, stimuli, delay)

    # Show dots
    dots = hf.create_dot_motion_stimulus(win, dot_params, direction, coherence)
    clock.reset()
    while clock.getTime() < gv['dot_display_time']:
        stimuli = [dot_outline, dots, no_dot_zone, fixation]
        hf.draw_all_stimuli(win, stimuli)

    # Show reference direction
    arc_CW = hf.draw_arc(win, dot_params['fieldSize'][0] / 2, reference, reference - 90, 'blue')
    arc_CCW = hf.draw_arc(win, dot_params['fieldSize'][0] / 2, reference, reference + 90, 'orange')
    ref_line = visual.Line(win, start=((dot_params['fieldSize'][0] / 2 - 30) * np.cos(np.deg2rad(reference)),
                                       (dot_params['fieldSize'][0] / 2 - 30) * np.sin(np.deg2rad(reference))),
                           end=((dot_params['fieldSize'][0] / 2 + 30) * np.cos(np.deg2rad(reference)),
                                (dot_params['fieldSize'][0] / 2 + 30) * np.sin(np.deg2rad(reference))),
                           lineColor='white', lineWidth=5)
    stimuli = [dot_outline, arc_CW, arc_CCW, ref_line, fixation]
    hf.draw_all_stimuli(win, stimuli)

    # Wait for participant response
    response, response_time = hf.check_key_press(win, gv['response_keys'])
    if response == gv['response_keys'][0]:
        chosen_direction = 'CW'
        fixation.color = 'blue'
    elif response == gv['response_keys'][1]:
        chosen_direction = 'CCW'
        fixation.color = 'orange'

    # Response visual feedback
    stimuli = [dot_outline, arc_CW, arc_CCW, ref_line, fixation]
    hf.draw_all_stimuli(win, stimuli, 0.5)

    # Confidence rating on approximately a third of the trials
    if np.random.choice([True, False, False]):
        confidence_rating = hf.get_confidence_rating(win)

    # Clear the stimuli
    fixation.color = 'white'
    win.flip()
    core.wait(1)

# Close window
win.close()
core.quit()

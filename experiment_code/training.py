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
from psychopy import gui, visual, core, data, event, monitors
import helper_functions as hf
import ctypes  # for hiding the mouse cursor on Windows
import subprocess
import json

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
    n_trials=40,  # number of trials - 40 for training
    dot_display_time=1.0,  # duration of dot display, 1 second
    inter_trial_interval=[0.5, 1.0],  # duration of inter-trial interval, uniform distribution, 0.5-1 second
    response_keys=['o', 'p'],  # keys for CW and CCW responses
    low_coherence=0.5,  # low coherence - fixed at 0.5 for training
    high_coherence=0.5,  # high coherence - fixed at 0.5 for training
    low_distance=30,  # low distance - fixed at 30 for training
    high_distance=30,  # high distance - fixed at 30 for training
    bonus_factor=0.1  # bonus factor times correct responses
)

###################################
# DATA SAVING
###################################
# variables in info will be saved as participant data
info = dict(
    eeg=expInfo['eeg (y/n)'],
    expName=expName,
    curec_ID=curecID,
    session_nr=expInfo['session nr'],
    date=data.getDateStr(),
    start_time=None,
    end_time=None,

    participant=expInfo['participant nr'],
    age=expInfo['age'],
    gender=expInfo['gender (f/m/o)'],

    trial_count=0,  # trial counter
    coherence=None,  # coherence level, 'low' or 'high'
    distance=None,  # distance level, 'low' or 'high'
    direction=None,  # direction of motion
    reference_direction=None,  # reference direction, 'CW' or 'CCW'
    response=None,  # response, 'CW' or 'CCW'
    response_time=None,  # response time
)

# start a csv file for saving the participant data
log_vars = list(info.keys())
if not os.path.exists('data_training'):
    os.mkdir('data_training')
filename = os.path.join('data_training', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()

############################################
# SET UP WINDOW, MOUSE, EEG TRIGGERS, CLOCK
############################################
# WINDOW
mon = monitors.Monitor('maja_dell_1')
win = visual.Window(
    size=(1920, 1080),
    units="deg",
    screen=1,
    fullscr=True,
    color=(0.001, 0.001, 0.001),
    colorSpace='rgb',
    monitor=mon
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
big_txt = visual.TextStim(win=win, text='Welcome!', height=2, pos=[0, 3], color='white', wrapWidth=20, font='Monospace')
instructions_txt = visual.TextStim(win=win, text="\n\n\n\n\n\n Press SPACE to start.", height=1, pos=[0, 2], wrapWidth=30, color='white', font='Monospace')
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=1, pos=[0, 7.5], wrapWidth=30, color='white', font='Monospace')
dot_params = {  # parameters for dot-patch
    'units': 'deg',
    'nDots': 150,
    'dotSize': 9,
    'speed': 0.1,
    'fieldSize': [10, 10],
    'fieldShape': 'circle',
    'dotLife': -1,  # number of frames each dot lives for (-1=infinite)
    'signalDots': 'same',  # if ‘same’ then the signal and noise dots are constant. If ‘different’ then the choice of which is signal and which is noise gets randomised on each frame.
    'noiseDots': 'walk'  # ‘position’ = noise dots take a random position every frame; ‘direction’ = noise dots follow a random, but constant direction; ‘walk’ = noise dots vary their direction every frame, but keep a constant speed.
}
fixation = visual.TextStim(win, text='+', height=1.5, color='white')
no_dot_zone = visual.Circle(win, radius=0.5, edges=100, fillColor=(0.001, 0.001, 0.001))  # circle around fixation cross
dot_outline = visual.Circle(win, radius=dot_params['fieldSize'][0] / 2, edges=100, lineColor='white', lineWidth=5, fillColor=None)

###################################
# INSTRUCTIONS
###################################
# Welcome
big_txt.draw()
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

# Task
instructions_txt.text = (
    "In this task, you will see a cloud of dots moving in a certain direction. "
    "Afterward, a reference direction will be shown. Your task is to decide "
    "whether the overall direction of the dots was towards to the BLUE or the ORANGE side of the reference. "
    "To make your choice, press the BLUE or ORANGE button on the keyboard. The fixation cross will change to the colour of your choice.\n\n\n\n"
    "Press SPACE to continue."
)
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

instructions_txt.text = (
    "You will receive feedback during this practice. If your choice is correct, the fixation cross will turn green. "
    "If your choice is incorrect, the fixation cross will turn red.\n\n"
    f"There will be {gv['n_trials']} practice trials, which should be relatively easy.\n\n\n\n"
    "Press SPACE to begin."
)
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

###################################
# TASK
###################################
EEG_config.send_trigger(EEG_config.triggers['experiment_start'])
start_time = datetime.now()
info['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
correct_responses = 0

for trial in range(gv['n_trials']):
    trial += 1
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
    hf.exit_q(win)

    # Show dots
    dots = hf.create_dot_motion_stimulus(win, dot_params, direction, coherence)
    clock.reset()
    while clock.getTime() < gv['dot_display_time']:
        stimuli = [dot_outline, dots, no_dot_zone, fixation]
        hf.draw_all_stimuli(win, stimuli)
        hf.exit_q(win)

    # Show reference direction
    arc_CW = hf.draw_arc(win, dot_params['fieldSize'][0] / 2, reference, reference - 90, 'blue')
    arc_CCW = hf.draw_arc(win, dot_params['fieldSize'][0] / 2, reference, reference + 90, 'orange')
    ref_line = visual.Line(win, start=((dot_params['fieldSize'][0] / 2 - 1) * np.cos(np.deg2rad(reference)),
                                       (dot_params['fieldSize'][0] / 2 - 1) * np.sin(np.deg2rad(reference))),
                           end=((dot_params['fieldSize'][0] / 2 + 1) * np.cos(np.deg2rad(reference)),
                                (dot_params['fieldSize'][0] / 2 + 1) * np.sin(np.deg2rad(reference))),
                           lineColor='white', lineWidth=10)
    stimuli = [dot_outline, arc_CW, arc_CCW, ref_line, fixation]
    hf.draw_all_stimuli(win, stimuli)
    hf.exit_q(win)

    # Wait for participant response
    response, response_time = hf.check_key_press(win, gv['response_keys'])
    if response == gv['response_keys'][0]:
        chosen_direction = 'CW'
        fixation.color = 'blue'
    elif response == gv['response_keys'][1]:
        chosen_direction = 'CCW'
        fixation.color = 'orange'

    # Show the chosen direction color on fixation cross
    stimuli = [dot_outline, arc_CW, arc_CCW, ref_line, fixation]
    hf.draw_all_stimuli(win, stimuli, 0.5)
    hf.exit_q(win)

    # Determine if the response was correct and provide feedback
    if chosen_direction == reference_direction:
        correct_responses += 1
        fixation.color = 'lime'  # Correct choice
    else:
        fixation.color = 'red'  # Incorrect choice

    # Show the feedback color on the fixation cross
    stimuli = [dot_outline, fixation]
    hf.draw_all_stimuli(win, stimuli, 0.8)
    hf.exit_q(win)

    # Clear the stimuli
    fixation.color = 'white'
    win.flip()
    hf.exit_q(win)
    core.wait(1)

    # Save the data
    info['trial_count'] = trial
    info['coherence'] = coherence
    info['distance'] = distance
    info['direction'] = direction
    info['reference_direction'] = reference_direction
    info['response'] = chosen_direction
    info['response_time'] = response_time
    datafile.write(','.join([str(info[var]) for var in log_vars]) + '\n')
    datafile.flush()

# END
info['end_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
bonus = correct_responses * gv['bonus_factor']
instructions_txt.text = ("Well done! You have completed the training session.\n\n\n\n"
                         "Press SPACE to continue.")
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

# Convert the `info` dictionary to a JSON string
info_json = json.dumps(info)

# Call the next script, passing the JSON string as an argument
subprocess.run(['python', 'staircase.py', info_json])

# Close window
win.close()
core.quit()


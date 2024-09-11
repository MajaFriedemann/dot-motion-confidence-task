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
import sys
import json

print('Reminder: Press Q to quit.')

###################################
# SESSION INFO
###################################
# TASK VARIABLES
gv = dict(
    n_blocks=8,  # number of alternating calibration blocks - 240 staircase trials in total
    n_trials_per_block=30,  # number of trials per block
    dot_display_time=1.0,  # duration of dot display, 1 second
    inter_trial_interval=[0.5, 1.0],  # duration of inter-trial interval, uniform distribution, 0.5-1 second
    response_keys=['o', 'p'],  # keys for CW and CCW responses
    low_coherence=None,  # low coherence (0.5 * medium coherence)
    high_coherence=None,  # high coherence (2 * medium coherence)
    low_distance=None,  # low distance
    high_distance=None,  # high distance

    # staircase parameters
    medium_coherence=0.3,  # medium coherence ((low_coherence+high_coherence)/2) initialised at 0.3
    medium_distance=20,  # initial distance ((low_distance+high_distance)/2) initialised at 20
    coherence_step=0.01,  # step size for staircase
    distance_step=1,  # step size for staircase
)

###################################
# DATA SAVING
###################################
# Variables in info will be saved as participant data
# Retrieve the JSON string passed as an argument from training.py
info_json = sys.argv[1]
# Parse the JSON string back into a dictionary
info = json.loads(info_json)

# Start a CSV file for saving the participant data
log_vars = list(info.keys())
if not os.path.exists('data_staircase'):
    os.mkdir('data_staircase')
filename = os.path.join('data_staircase', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()

###################################
# SET UP WINDOW, MOUSE, EEG TRIGGERS, CLOCK
###################################
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
send_triggers = info['eeg'].lower() == 'y'
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
# Task reminder
instructions_txt.text = ("You have completed the training session! Now, it will become more difficult to estimate the net direction of dot motion. "
                         "It is meant to be difficult, so please do not worry if you find it hard. \n\n"
                         f"You will no longer receive feedback. There will be {gv['n_trials_per_block'] * gv['n_blocks']} trials.\n\n\n\n"
                         "Press SPACE to continue.")
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
correct_count = 0
is_coherence_block = False  # Start with coherence calibration block (gets changed at the start of the first block)

for block in range(gv['n_blocks']):
    is_coherence_block = not is_coherence_block  # Alternate between coherence and distance blocks

    for trial in range(gv['n_trials_per_block']):
        trial += 1
        # Set the direction, coherence, and reference direction for the trial
        direction = round(np.random.uniform(1, 360), 2)  # Randomly choose motion direction

        if is_coherence_block:
            coherence = gv['medium_coherence']  # Use medium coherence for coherence blocks
            distance = gv['medium_distance']  # Use medium distance for coherence blocks
        else:
            # For distance blocks, randomly choose low or high distance
            if np.random.choice([True, False]):
                distance = gv['high_distance']
            else:
                distance = gv['low_distance']
            # Use corresponding coherence level based on chosen distance
            coherence = gv['high_coherence'] if distance == gv['low_distance'] else gv['low_coherence']

        # Randomly determine if the reference direction is clockwise (CW) or counterclockwise (CCW)
        if np.random.choice([True, False]):
            reference_direction = 'CW'
            reference = (direction + distance) % 360  # Calculate reference direction for CW
        else:
            reference_direction = 'CCW'
            reference = (direction - distance) % 360  # Calculate reference direction for CCW

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
            fixation.color = 'blue'  # Feedback: Fixation cross turns blue for CW
        elif response == gv['response_keys'][1]:
            chosen_direction = 'CCW'
            fixation.color = 'orange'  # Feedback: Fixation cross turns orange for CCW
        # Staircasing procedure
        # If the participant's response is correct
        if chosen_direction == reference_direction:
            correct_responses += 1
            correct_count += 1
            # Apply the two-down-one-up rule
            if correct_count == 2:
                correct_count = 0
                if is_coherence_block:
                    # Decrease medium coherence if in a coherence block
                    gv['medium_coherence'] = max(gv['medium_coherence'] - gv['coherence_step'], 0.01)
                else:
                    # Decrease medium distance if in a distance block
                    gv['medium_distance'] = max(gv['medium_distance'] - gv['distance_step'], 1)
        else:
            # If the response is incorrect, reset correct count and increase the corresponding staircase variable
            correct_count = 0
            if is_coherence_block:
                # Increase medium coherence if in a coherence block
                gv['medium_coherence'] = min(gv['medium_coherence'] + gv['coherence_step'], 1)
            else:
                # Increase medium distance if in a distance block
                gv['medium_distance'] = min(gv['medium_distance'] + gv['distance_step'], 50)

        # Adjust low and high coherence and distance based on the new medium values
        gv['low_coherence'] = gv['medium_coherence'] * 0.5
        gv['high_coherence'] = gv['medium_coherence'] * 2
        gv['low_distance'] = gv['medium_distance'] * 0.5
        gv['high_distance'] = gv['medium_distance'] * 2

        # Response visual feedback
        stimuli = [dot_outline, arc_CW, arc_CCW, ref_line, fixation]
        hf.draw_all_stimuli(win, stimuli, 0.5)
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
        info['block_type'] = 'coherence' if is_coherence_block else 'distance'
        info['low_coherence'] = gv['low_coherence']
        info['high_coherence'] = gv['high_coherence']
        info['low_distance'] = gv['low_distance']
        info['high_distance'] = gv['high_distance']
        datafile.write(','.join([str(info[var]) for var in log_vars]) + '\n')
        datafile.flush()

# END
info['end_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
instructions_txt.text = ("Well done! You have completed the task. \n\n")
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

# Close window
win.close()
core.quit()

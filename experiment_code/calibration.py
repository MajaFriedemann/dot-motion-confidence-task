"""
calibration for random dot motion task with confidence ratings
coherences and distances get calibrated in alternating blocks using 2-down-1-up
whenever the distance gets calibrated, the coherence is set to the medium value
whenever the coherence gets calibrated, the distance is set to the medium value
saves data in calibration_data folder

Maja Friedemann 2025
"""

###################################
# IMPORT PACKAGES
###################################
import numpy as np
import os
from datetime import datetime
from psychopy import gui, visual, core, data, event, monitors
import pandas as pd  # For reading Excel files
import ctypes  # For hiding the mouse cursor on Windows

import helper_functions as hf
from RDK_3_sets import create_dot_motion_stimulus_n_sets

print('Reminder: Press Q to quit.')

###################################
# SESSION INFO
###################################
expName = 'confidence-pgACC-TUS'
curecID = 'R88533/RE002'
expInfo = {
    'participant nr': '999',
    'eeg (y/n)': 'n',
    'session nr': '1',
    'age': '',
    'gender (f/m/o)': '',
}

dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if not dlg.OK:
    core.quit()

###################################
# TASK (STRUCTURE) VARIABLES
###################################
# These do NOT get written to each trial row by default, but define how the task is structured and calibrated
gv = dict(
    # Timing and general
    dot_display_time=1.0,  # duration of dot display (seconds)
    inter_trial_interval=[0.5, 1.0],  # uniform distribution from 0.5–1s
    response_keys=['d', 'k'],  # keys for blue/orange responses

    # Staircase / calibration settings
    n_blocks=8,  # number of alternating calibration blocks 8
    n_trials_per_block=30,  # total = n_blocks * n_trials_per_block 30
    medium_coherence=0.3,  # initial guess for "medium" coherence
    medium_distance=20,  # initial guess for "medium" distance
    coherence_step=0.01,  # staircase step size for coherence (2-down-1-up)
    distance_step=1,  # staircase step size for distance (2-down-1-up)

    # Will be updated dynamically after each trial
    low_coherence=None,
    high_coherence=None,
    low_distance=None,
    high_distance=None
)

###################################
# DATA (TO-BE-SAVED) VARIABLES
###################################
# These WILL be written into each row of the CSV
info = dict(
    expName=expName,
    curec_ID=curecID,
    session_nr=expInfo['session nr'],
    date=data.getDateStr(),
    start_time=None,
    end_time=None,
    duration=None,

    participant=expInfo['participant nr'],
    age=expInfo['age'],
    gender=expInfo['gender (f/m/o)'],

    trial_count=0,

    # Per-trial calibration values
    coherence=None,  # numeric coherence
    coherence_level=None,  # 'low', 'medium', or 'high'
    distance=None,  # numeric distance
    distance_level=None,  # 'low', 'medium', or 'high'

    direction=None,  # motion direction (numeric)
    reference=None,  # numeric angle for boundary
    signal_delay=None,  # in seconds

    correct_response=None,  # 'CW' or 'CCW'
    participant_response=None,  # 'CW' or 'CCW'
    correct=None,  # True/False
    correct_response_colour=None,
    participant_response_colour=None,

    response_time=None,  # time to respond
    confidence_start_position=None,  # 50-100
    confidence_rating=None,  # 50–100 (not used in calibration)
    confidence_response_time=None,
    confidence_adjustments_steps=None,
    confidence_adjustments_times=None,

    # We'll store the final calibration in these fields for the last row
    final_low_coherence=None,
    final_high_coherence=None,
    final_low_distance=None,
    final_high_distance=None
)

# List of columns to write in the CSV
log_vars = list(info.keys())

if not os.path.exists('calibration_data'):
    os.mkdir('calibration_data')

filename = os.path.join(
    'calibration_data',
    f"{info['participant']}_{info['session_nr']}_{info['date']}"
)
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()

############################################
# SET UP WINDOW, MOUSE, EEG TRIGGERS, CLOCK
############################################
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
frame_rate = win.getActualFrameRate()
if frame_rate is None or frame_rate < 1:
    print("Warning: Could not determine frame rate. Defaulting to 60 Hz.")
    frame_rate = 60

win.setMouseVisible(False)
mouse = event.Mouse(visible=False, win=win)
mouse.setVisible(False)
if os.name == 'nt':
    ctypes.windll.user32.ShowCursor(False)

# EEG triggers
triggers = dict(
    experiment_start=1,
    trial_start=2,
    dots_onset=3,
    signal_onset=4,
    reference_onset=5,
    response_made=6,
    confidence_rating_onset=7,
    confidence_increase=8,
    confidence_decrease=9,
    confidence_response_made=10,
    experiment_end=11
)
send_triggers = expInfo['eeg (y/n)'].lower() == 'y'
EEG_config = hf.EEGConfig(triggers, send_triggers)

# CLOCK
clock = core.Clock()

###################################
# CREATE STIMULI
###################################
big_txt = visual.TextStim(
    win=win,
    text='Welcome!',
    height=2,
    pos=[0, 3],
    color='white',
    wrapWidth=20,
    font='Arial'
)
instructions_txt = visual.TextStim(
    win=win,
    text="\n\n\n\n\n\n Press SPACE to start.",
    height=1,
    pos=[0, 2],
    wrapWidth=30,
    color='white',
    font='Arial'
)
dot_parameters = {
    'n_dot_sets': 3,
    'random_dot_behaviour': 'random_position',
    'duration': gv['dot_display_time'],
    'aperture_diameter': 11,
    'fixation_diameter': 0.45,
    'dot_diameter': 0.16,
    'dot_density': 1,
    'speed': 2
}
aperture_outline = visual.Circle(
    win,
    radius=dot_parameters['aperture_diameter'] / 2,
    edges=100,
    lineColor='white',
    lineWidth=5,
    units='deg',
    fillColor=None
)
fixation = visual.ShapeStim(
    win,
    vertices=[
        (-dot_parameters['fixation_diameter'] / 2, 0),
        (dot_parameters['fixation_diameter'] / 2, 0),
        (0, 0),
        (0, dot_parameters['fixation_diameter'] / 2),
        (0, -dot_parameters['fixation_diameter'] / 2)
    ],
    lineWidth=4,
    closeShape=False,
    lineColor='white'
)
blue_circle = visual.Circle(
    win,
    radius=0.3,
    pos=(-9, 0),  # Left side of the screen
    fillColor='blue',
    lineColor=None,
    units='deg'
)
orange_circle = visual.Circle(
    win,
    radius=0.3,
    pos=(9, 0),  # Right side of the screen
    fillColor='orange',
    lineColor=None,
    units='deg'
)

###################################
# INSTRUCTIONS
###################################
instructions_txt.text = (
    "You have completed the training session!\n\n"
    "The task will now continue without feedback and without confidence ratings. "
    "It will become more difficult to estimate the direction of dot motion. "
    "Try to be as accurate as possible.\n\n"
    f"There will be {gv['n_blocks'] * gv['n_trials_per_block']} trials in total.\n\n"
    "Press SPACE to start."
)
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # Show instructions until space is pressed
event.clearEvents()

###################################
# TASK WITH 2-DOWN-1-UP
###################################
EEG_config.send_trigger(triggers['experiment_start'])
start_time = datetime.now()
info['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")

correct_responses = 0
correct_count = 0  # for 2-down-1-up
is_coherence_block = False  # Flip True/False each block
trial_overall_count = 0

# Initialize low/high from the initial "medium" guess
gv['low_coherence'] = gv['medium_coherence'] * 0.5
gv['high_coherence'] = gv['medium_coherence'] * 2.0
gv['low_distance'] = gv['medium_distance'] * 0.5
gv['high_distance'] = gv['medium_distance'] * 2.0

for block_i in range(gv['n_blocks']):
    # Alternate between calibrating coherence and distance
    is_coherence_block = not is_coherence_block
    block_type = 'coherence' if is_coherence_block else 'distance'
    print(f"\n=== Starting Block {block_i + 1}/{gv['n_blocks']} ({block_type} calibration) ===")

    for trial_in_block in range(gv['n_trials_per_block']):
        trial_overall_count += 1
        EEG_config.send_trigger(triggers['trial_start'])

        # -------------------------
        # 1) Choose coherence/distance
        # -------------------------
        if is_coherence_block:
            # For coherence blocks: use "medium" coherence, "medium" distance
            coherence_val = gv['medium_coherence']
            distance_val = gv['medium_distance']
            coherence_level = "medium"
            distance_level = "medium"
        else:
            # For distance blocks: pick low or high distance
            if np.random.choice([True, False]):
                distance_val = gv['high_distance']
                distance_level = "high"
            else:
                distance_val = gv['low_distance']
                distance_level = "low"

            # Then pick coherence accordingly
            if distance_val == gv['low_distance']:
                # Distance is low => coherence is high
                coherence_val = gv['high_coherence']
                coherence_level = "high"
            else:
                # Distance is high => coherence is low
                coherence_val = gv['low_coherence']
                coherence_level = "low"

        # -------------------------
        # 2) Random direction & signal delay
        # -------------------------
        direction = round(np.random.uniform(1, 360), 0)
        signal_delay = np.random.uniform(0.4, 0.8)

        # Decide reference (CW or CCW offset by distance)
        if np.random.choice([True, False]):
            reference_direction = 'CW'
            reference_angle = (direction + distance_val) % 360
        else:
            reference_direction = 'CCW'
            reference_angle = (direction - distance_val) % 360

        print(
            f"Trial {trial_overall_count}: block={block_i + 1}, block_type={block_type}, "
            f"direction={direction}, coherence={coherence_val:.3f}({coherence_level}), "
            f"distance={distance_val:.3f}({distance_level}), reference={reference_angle:.3f}"
        )

        # -------------------------
        # 3) Fixation
        # -------------------------
        stimuli = [aperture_outline, fixation]
        delay_time = np.random.uniform(gv['inter_trial_interval'][0], gv['inter_trial_interval'][1])
        hf.draw_all_stimuli(win, stimuli, wait=delay_time)
        hf.exit_q(win)

        # -------------------------
        # 4) Show dots
        # -------------------------
        EEG_config.send_trigger(triggers['dots_onset'])
        create_dot_motion_stimulus_n_sets(
            win, frame_rate, direction, coherence_val, signal_delay, dot_parameters, EEG_config
        )

        # -------------------------
        # 5) Show reference arcs
        # -------------------------
        if 0 <= reference_angle < 180:
            arc_CW_color = 'orange'
            arc_CCW_color = 'blue'
        else:
            arc_CW_color = 'blue'
            arc_CCW_color = 'orange'

        arc_CW = hf.draw_arc(
            win, dot_parameters['aperture_diameter'] / 2,
            reference_angle, reference_angle - 90, arc_CW_color
        )
        arc_CCW = hf.draw_arc(
            win, dot_parameters['aperture_diameter'] / 2,
            reference_angle, reference_angle + 90, arc_CCW_color
        )
        ref_line = visual.Line(
            win,
            start=(
                (dot_parameters['aperture_diameter'] / 2 - 1) * np.cos(np.deg2rad(reference_angle)),
                (dot_parameters['aperture_diameter'] / 2 - 1) * np.sin(np.deg2rad(reference_angle))
            ),
            end=(
                (dot_parameters['aperture_diameter'] / 2 + 1) * np.cos(np.deg2rad(reference_angle)),
                (dot_parameters['aperture_diameter'] / 2 + 1) * np.sin(np.deg2rad(reference_angle))
            ),
            lineColor='white', lineWidth=6
        )
        stimuli = [aperture_outline, arc_CW, arc_CCW, ref_line, fixation, blue_circle, orange_circle]
        EEG_config.send_trigger(triggers['reference_onset'])
        hf.draw_all_stimuli(win, stimuli, wait=0.01)
        hf.exit_q(win)

        # -------------------------
        # 6) Response
        # -------------------------
        response_key, response_time = hf.check_key_press(win, gv['response_keys'])
        EEG_config.send_trigger(triggers['response_made'])

        # Map participant's key press to 'CW' or 'CCW'
        if 0 <= reference_angle < 180:
            if response_key == gv['response_keys'][0]:
                chosen_direction = 'CCW'
                participant_color = 'blue'
            else:
                chosen_direction = 'CW'
                participant_color = 'orange'
        else:
            if response_key == gv['response_keys'][0]:
                chosen_direction = 'CW'
                participant_color = 'blue'
            else:
                chosen_direction = 'CCW'
                participant_color = 'orange'

        fixation.color = participant_color
        is_correct = (chosen_direction == reference_direction)
        if is_correct:
            correct_responses += 1
            correct_count += 1
            if correct_count == 2:
                correct_count = 0
                if is_coherence_block:
                    gv['medium_coherence'] = max(gv['medium_coherence'] - gv['coherence_step'], 0.01)
                else:
                    gv['medium_distance'] = max(gv['medium_distance'] - gv['distance_step'], 1)
        else:
            correct_count = 0
            if is_coherence_block:
                gv['medium_coherence'] = min(gv['medium_coherence'] + gv['coherence_step'], 1)
            else:
                gv['medium_distance'] = min(gv['medium_distance'] + gv['distance_step'], 50)

        # Update low/high after each trial
        gv['low_coherence'] = gv['medium_coherence'] * 0.5
        gv['high_coherence'] = gv['medium_coherence'] * 2.0
        gv['low_distance'] = gv['medium_distance'] * 0.5
        gv['high_distance'] = gv['medium_distance'] * 2.0

        # Determine correct color for logging
        if reference_direction == 'CW':
            correct_color = arc_CW_color
        else:
            correct_color = arc_CCW_color

        # (Optional) brief feedback
        stimuli = [aperture_outline, fixation, blue_circle, orange_circle]
        hf.draw_all_stimuli(win, stimuli, wait=0.5)
        hf.exit_q(win)

        # -------------------------
        # 7) Confidence rating (disabled in calibration)
        # -------------------------
        confidence_start_position = None
        confidence_rating = None
        confidence_response_time = None
        confidence_adjustments = None

        # -------------------------
        # 8) Clear & wait
        # -------------------------
        fixation.color = 'white'
        win.flip()
        hf.exit_q(win)
        core.wait(1)

        # -------------------------
        # 9) SAVE DATA for this trial
        # -------------------------
        info['trial_count'] = trial_overall_count

        info['coherence'] = coherence_val
        info['coherence_level'] = coherence_level
        info['distance'] = distance_val
        info['distance_level'] = distance_level

        info['direction'] = direction
        info['reference'] = reference_angle
        info['signal_delay'] = signal_delay

        info['correct_response'] = reference_direction
        info['participant_response'] = chosen_direction
        info['correct'] = is_correct
        info['correct_response_colour'] = correct_color
        info['participant_response_colour'] = participant_color

        info['response_time'] = response_time
        info['confidence_start_position'] = confidence_start_position
        info['confidence_rating'] = confidence_rating
        info['confidence_response_time'] = confidence_response_time
        if confidence_adjustments is not None:
            info['confidence_adjustments_steps'] = confidence_adjustments['step_list']
            info['confidence_adjustments_times'] = confidence_adjustments['time_list']
        else:
            info['confidence_adjustments_steps'] = None
            info['confidence_adjustments_times'] = None

        datafile.write(','.join(str(info[var]) for var in log_vars) + '\n')
        datafile.flush()

# End of all blocks/trials
EEG_config.send_trigger(triggers['experiment_end'])
end_time = datetime.now()
info['end_time'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
duration = end_time - start_time
info['duration'] = str(duration)

# Store the final calibration values in `info` for the last CSV row
info['final_low_coherence'] = gv['low_coherence']
info['final_high_coherence'] = gv['high_coherence']
info['final_low_distance'] = gv['low_distance']
info['final_high_distance'] = gv['high_distance']

# Overwrite the final row with updated info (including final calibration)
if info['trial_count'] > 0:
    datafile.close()
    with open(filename + '.csv', 'r+') as datafile:
        lines = datafile.readlines()
        # Replace last line with the updated final info
        lines[-1] = ','.join(str(info[var]) for var in log_vars) + '\n'
        datafile.seek(0)
        datafile.writelines(lines)
        datafile.flush()

instructions_txt.text = (
    "Well done! \n\nYou have completed the task.\n\n"
)
instructions_txt.draw()
win.flip()
hf.exit_q(win)
keys = event.waitKeys(keyList=['space'], maxWait=10)
event.clearEvents()
win.close()
core.quit()

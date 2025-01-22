"""
training for random dot motion task with confidence ratings
coherences and distances are set to something easy instead of taking the calibrated values
includes more instructions
gives trial by trial feedback
saves data in training_data folder

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
# TASK VARIABLES
###################################
gv = dict(
    n_trials=20,  # number of trials for training
    dot_display_time=1.0,  # duration of dot display (in seconds)
    inter_trial_interval=[0.5, 1.0],  # uniform distribution from 0.5–1s
    response_keys=['d', 'k'],  # keys for blue/orange responses
    low_coherence=0.5,  # easy for training
    high_coherence=0.7,  # easy for training
    low_distance=30,   # easy for training
    high_distance=50,  # easy for training
)

###################################
# DATA SAVING
###################################
# All the variables we want to track
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

    # coherence/distance numeric & string labels
    coherence=None,         # numeric coherence
    coherence_level=None,   # 'low' or 'high'
    distance=None,          # numeric distance
    distance_level=None,    # 'low' or 'high'

    direction=None,         # motion direction (numeric)
    reference=None,         # numeric angle for boundary
    signal_delay=None,      # in seconds

    correct_response=None,        # 'CW' or 'CCW'
    participant_response=None,    # 'CW' or 'CCW'
    correct=None,                # True/False
    correct_response_colour=None,
    participant_response_colour=None,

    response_time=None,           # time to respond
    confidence_start_position=None,  # 50-100
    confidence_rating=None,       # 50–100
    confidence_response_time=None,
    confidence_adjustments_steps=None,
    confidence_adjustments_times=None,
)

# Create a CSV file with these columns in order
log_vars = list(info.keys())
if not os.path.exists('training_data'):
    os.mkdir('training_data')
filename = os.path.join('training_data', f"{info['participant']}_{info['session_nr']}_{info['date']}")
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
if os.name == 'nt':  # Hide cursor on Windows
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
instructions_top_txt = visual.TextStim(
    win=win,
    text="Instructions",
    height=1,
    pos=[0, 7.5],
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
big_txt.draw()
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])
event.clearEvents()

# Task introduction
instructions_txt.text = (
    "Welcome to the dot motion task! In this experiment, you'll see moving dots appearing within a circle. "
    "Your task will be to carefully observe their overall direction of motion and make a judgment about it afterwards. "
    "Try to keep your eyes focused on the central cross throughout each trial, as this will help you perceive the motion better.\n\n"
    "Press SPACE to learn about making your responses."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])
event.clearEvents()

# Response instructions
instructions_txt.text = (
    "After the dots disappear, you'll see a reference line that divides the circle into two zones - one blue and one orange. "
    "Your task is to indicate whether the dots were moving toward the blue or orange zone. "
    "To respond, you'll use two keys on the keyboard: press the BLUE key with your left hand to choose blue, or press the ORANGE key with your "
    "right hand to choose orange. Circles on the left and right side of the screen will remind you of the key-colour mapping. "
    "After you make your choice, the central cross will change colour to show your selection.\n\n"
    "Press SPACE to learn about confidence ratings."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])
event.clearEvents()

# Confidence instructions
instructions_txt.text = (
    "Every now and then, you'll be asked how confident you are in your decision. "
    "You'll see a scale ranging from 50% to 100%. A rating of 50% means you were completely guessing on your most recent trial, "
    "while 100% means you were absolutely certain about the response. "
    "The slider marker will start at a random position on the scale. You can adjust it using the same blue and orange response keys "
    "to move left or right on the scale. Then press SPACE to confirm your rating.\n\n"
    "Press SPACE to learn about the practice session."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])
event.clearEvents()

# Practice session instructions
instructions_txt.text = (
    f"You will now complete {gv['n_trials']} practice trials to help you get familiar with the task. "
    "During these practice trials, you'll receive feedback after each response. The central cross will turn "
    "green if your answer was correct, or red if it was incorrect. Try to focus on the overall pattern of the "
    "dots' motion and respond as accurately as you can. When rating your confidence, be honest about how sure "
    "you felt about each decision.\n\n"
    "Press SPACE when you're ready to begin."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])
event.clearEvents()

###################################
# TASK
###################################
EEG_config.send_trigger(EEG_config.triggers['experiment_start'])
start_time = datetime.now()
info['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
correct_responses = 0

for trial in range(gv['n_trials']):
    EEG_config.send_trigger(EEG_config.triggers['trial_start'])
    trial_num = trial + 1

    # 1) Choose signal_delay, direction, coherence, distance
    signal_delay = np.random.uniform(0.4, 0.8)
    direction = round(np.random.uniform(1, 360), 0)

    # Determine coherence numeric & level
    if np.random.choice([True, False]):  # randomly pick high or low
        coherence_val = gv['high_coherence']
        coherence_level = 'high'
    else:
        coherence_val = gv['low_coherence']
        coherence_level = 'low'

    # Determine distance numeric & level
    if np.random.choice([True, False]):
        distance_val = gv['high_distance']
        distance_level = 'high'
    else:
        distance_val = gv['low_distance']
        distance_level = 'low'

    # 2) Decide the correct reference side
    if np.random.choice([True, False]):
        reference_direction = 'CW'
        reference_angle = (direction + distance_val) % 360
    else:
        reference_direction = 'CCW'
        reference_angle = (direction - distance_val) % 360

    print(
        f"Trial {trial_num}: direction={direction}, "
        f"coherence={coherence_val}({coherence_level}), "
        f"distance={distance_val}({distance_level}), reference={reference_angle}"
    )

    # 3) Show fixation cross
    stimuli = [aperture_outline, fixation]
    delay_time = np.random.uniform(gv['inter_trial_interval'][0], gv['inter_trial_interval'][1])
    hf.draw_all_stimuli(win, stimuli, delay_time)
    hf.exit_q(win)

    # 4) Show dots
    EEG_config.send_trigger(EEG_config.triggers['dots_onset'])
    create_dot_motion_stimulus_n_sets(
        win, frame_rate, direction, coherence_val, signal_delay, dot_parameters, EEG_config
    )

    # 5) Show reference direction (split arcs)
    # Decide arc colors
    if 0 <= reference_angle < 180:
        arc_CW_color = 'orange'
        arc_CCW_color = 'blue'
    else:
        arc_CW_color = 'blue'
        arc_CCW_color = 'orange'

    arc_CW = hf.draw_arc(win, dot_parameters['aperture_diameter'] / 2, reference_angle, reference_angle - 90, arc_CW_color)
    arc_CCW = hf.draw_arc(win, dot_parameters['aperture_diameter'] / 2, reference_angle, reference_angle + 90, arc_CCW_color)
    ref_line = visual.Line(
        win,
        start=((dot_parameters['aperture_diameter'] / 2 - 1) * np.cos(np.deg2rad(reference_angle)),
               (dot_parameters['aperture_diameter'] / 2 - 1) * np.sin(np.deg2rad(reference_angle))),
        end=((dot_parameters['aperture_diameter'] / 2 + 1) * np.cos(np.deg2rad(reference_angle)),
             (dot_parameters['aperture_diameter'] / 2 + 1) * np.sin(np.deg2rad(reference_angle))),
        lineColor='white', lineWidth=6
    )
    stimuli = [aperture_outline, arc_CW, arc_CCW, ref_line, fixation, blue_circle, orange_circle]
    EEG_config.send_trigger(EEG_config.triggers['reference_onset'])
    hf.draw_all_stimuli(win, stimuli)
    hf.exit_q(win)

    # 6) Response
    response_key, response_time = hf.check_key_press(win, gv['response_keys'])
    EEG_config.send_trigger(EEG_config.triggers['response_made'])

    # Map participant's key press to 'CW' or 'CCW'
    if 0 <= reference_angle < 180:
        # reference in top half
        if response_key == gv['response_keys'][0]:
            chosen_direction = 'CCW'
            participant_color = 'blue'
        else:
            chosen_direction = 'CW'
            participant_color = 'orange'
    else:
        # reference in bottom half
        if response_key == gv['response_keys'][0]:
            chosen_direction = 'CW'
            participant_color = 'blue'
        else:
            chosen_direction = 'CCW'
            participant_color = 'orange'
    fixation.color = participant_color

    # Check correctness
    is_correct = (chosen_direction == reference_direction)
    if is_correct:
        correct_responses += 1

    # Determine the color for the correct side
    if reference_direction == 'CW':
        correct_color = arc_CW_color
    else:
        correct_color = arc_CCW_color

    # 7) Feedback
    stimuli = [aperture_outline, fixation, blue_circle, orange_circle]
    hf.draw_all_stimuli(win, stimuli, 0.5)
    hf.exit_q(win)

    # Because this is the training, we also give feedback on correctness
    if is_correct:
        fixation.color = 'lime'
    else:
        fixation.color = 'red'
    stimuli = [aperture_outline, fixation, blue_circle, orange_circle]
    hf.draw_all_stimuli(win, stimuli, 1)
    hf.exit_q(win)

    # 8) Confidence rating (random 1/3 of trials)
    confidence_start_position = None
    confidence_rating = None
    confidence_response_time = None
    confidence_adjustments = None
    if np.random.choice([True, False, False]):
        confidence_rating, confidence_response_time, confidence_start_position, confidence_adjustments = hf.get_confidence_rating(
            win, gv, EEG_config)

    # 9) Clear & wait
    fixation.color = 'white'
    win.flip()
    hf.exit_q(win)
    core.wait(1)

    # 10) SAVE DATA for this trial
    info['trial_count'] = trial_num

    info['coherence'] = coherence_val
    info['coherence_level'] = coherence_level
    info['distance'] = distance_val
    info['distance_level'] = distance_level

    info['direction'] = direction
    info['reference'] = reference_angle
    info['signal_delay'] = signal_delay

    info['correct_response'] = reference_direction  # 'CW'/'CCW'
    info['participant_response'] = chosen_direction  # 'CW'/'CCW'
    info['correct'] = is_correct  # True/False

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

# END OF ALL TRIALS
EEG_config.send_trigger(EEG_config.triggers['experiment_end'])
end_time = datetime.now()
info['end_time'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
duration = end_time - start_time
info['duration'] = str(duration)

instructions_txt.text = (
    "Well done! You have completed the training.\n\n"
    f"You made {correct_responses} correct responses out of {gv['n_trials']} trials.\n\n"
    f"If you have any questions about the task, please ask the experimenter now."
)
instructions_txt.draw()
win.flip()

# Overwrite the final row with experiment-level info
if info['trial_count'] > 0:
    datafile.close()
    with open(filename + '.csv', 'r+') as datafile:
        lines = datafile.readlines()
        # Replace last line with updated final info
        lines[-1] = ','.join(str(info[var]) for var in log_vars) + '\n'
        datafile.seek(0)
        datafile.writelines(lines)
        datafile.flush()

hf.exit_q(win)
core.wait(10)
win.close()
core.quit()

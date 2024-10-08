###################################
# IMPORT PACKAGES
###################################
import numpy as np
import os
from datetime import datetime
from psychopy import gui, visual, core, data, event, monitors
import ctypes  # for hiding the mouse cursor on Windows

import helper_functions as hf
from RDK_3_sets import create_dot_motion_stimulus_n_sets

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
    n_trials=300,  # number of trials - 300
    dot_display_time=1.0,  # duration of dot display, 1 second
    inter_trial_interval=[0.5, 1.0],  # duration of inter-trial interval, uniform distribution, 0.5-1 second
    response_keys=['o', 'p'],  # keys for CW and CCW responses
    low_coherence=0.2,  # low coherence - needs to be calibrated to the participant
    high_coherence=0.4,  # high coherence - needs to be calibrated to the participant
    low_distance=10,  # low distance - needs to be calibrated to the participant
    high_distance=30,  # high distance - needs to be calibrated to the participant
    bonus_factor=0.1  # bonus factor times correct responses
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

    trial_count=0,  # trial counter
    coherence=None,  # coherence level, 'low' or 'high'
    distance=None,  # distance level, 'low' or 'high'
    direction=None,  # direction of motion
    reference_direction=None,  # reference direction, 'CW' or 'CCW'
    response=None,  # response, 'CW' or 'CCW'
    response_time=None,  # response time
    confidence_rating=None,  # confidence rating
    confidence_response_time=None,  # confidence response time
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
dot_parameters = {
    'n_dot_sets': 3,
    'random_dot_behaviour': 'random_position',
    'duration': gv['dot_display_time'],
    'aperture_diameter': 8,
    'fixation_diameter': 0.4,
    'dot_diameter': 0.16,
    'dot_density': 1,
    'speed': 2
}
aperture_outline = visual.Circle(
        win,
        radius=dot_parameters['aperture_diameter'] / 2,
        edges=100,
        lineColor='white',  # White outline
        lineWidth=5,  # Line thickness
        units='deg',
        fillColor=None  # No fill, just an outline
    )
fixation = visual.ShapeStim(
        win,
        vertices=[(-dot_parameters['fixation_diameter'] / 2, 0), (dot_parameters['fixation_diameter'] / 2, 0), (0, 0), 
                  (0, dot_parameters['fixation_diameter'] / 2), (0, -dot_parameters['fixation_diameter'] / 2)],
        lineWidth=4,
        closeShape=False,
        lineColor='white'
    )

###################################
# INSTRUCTIONS
###################################
# Welcome
big_txt.draw()
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # Show instructions until SPACE is pressed
event.clearEvents()

# Task reminder
instructions_txt.text = (
    "You are now ready for the confidence task.\n\n"
    "As a reminder, you will see a cloud of dots moving in a certain direction. "
    "After that, a reference direction will be shown. Your task is to decide "
    "whether the overall direction of the dots was closer to the BLUE or the ORANGE side of the reference. "
    "To make your choice, press the BLUE or ORANGE button on the keyboard. The fixation cross will change to the colour of your choice.\n\n\n\n"
    "Press SPACE to continue."
)
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # Show instructions until SPACE is pressed
event.clearEvents()

# Confidence reminder
instructions_txt.text = (
    "In some trials, you will be asked to rate your confidence in your decision on a scale from 50% to 100%.\n\n"
    "The slider will start at a random position. Use the response keys to move the slider, and press SPACE to confirm your response.\n\n"
    "To maximize your bonus, aim to make as many correct decisions as possible and accurately estimate your confidence.\n\n\n\n"
    "Press SPACE to begin."
)
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # Show instructions until SPACE is pressed
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
    stimuli = [aperture_outline, fixation]
    delay = np.random.uniform(gv['inter_trial_interval'][0], gv['inter_trial_interval'][1])
    hf.draw_all_stimuli(win, stimuli, delay)
    hf.exit_q(win)

    # Show dots
    create_dot_motion_stimulus_n_sets(win, frame_rate, 180, 0.5, dot_parameters)

    # Show reference direction
    arc_CW = hf.draw_arc(win, dot_parameters['aperture_diameter'] / 2, reference, reference - 90, 'blue')
    arc_CCW = hf.draw_arc(win, dot_parameters['aperture_diameter'] / 2, reference, reference + 90, 'orange')
    ref_line = visual.Line(win, start=((dot_parameters['aperture_diameter'] / 2 - 1) * np.cos(np.deg2rad(reference)),
                                       (dot_parameters['aperture_diameter'] / 2 - 1) * np.sin(np.deg2rad(reference))),
                           end=((dot_parameters['aperture_diameter'] / 2 + 1) * np.cos(np.deg2rad(reference)),
                                (dot_parameters['aperture_diameter'] / 2 + 1) * np.sin(np.deg2rad(reference))),
                           lineColor='white', lineWidth=6)
    stimuli = [aperture_outline, arc_CW, arc_CCW, ref_line, fixation]
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
    if chosen_direction == reference_direction:
        correct_responses += 1

    # Response visual feedback
    stimuli = [aperture_outline, arc_CW, arc_CCW, ref_line, fixation]
    hf.draw_all_stimuli(win, stimuli, 0.5)
    hf.exit_q(win)

    # Confidence rating on approximately a third of the trials  # MAJA - make this every trial?
    confidence_rating = None
    confidence_response_time = None
    if np.random.choice([True, False, False]):
        confidence_rating, confidence_response_time = hf.get_confidence_rating(win, gv)

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
    info['confidence_rating'] = confidence_rating
    info['confidence_response_time'] = confidence_response_time
    datafile.write(','.join([str(info[var]) for var in log_vars]) + '\n')
    datafile.flush()

# END
info['end_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
bonus = correct_responses * gv['bonus_factor']
instructions_txt.text = ("Well done! You have completed the task. \n\n"
                         f"You made {correct_responses} correct responses out of {gv['n_trials']} trials. \n\n"
                         f"Your bonus is £{bonus}. \n\n")
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

# Close window
win.close()
core.quit()

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
# TASK VARIABLES
###################################
gv = dict(
    dot_display_time=1.0,          # duration of dot display (seconds)
    inter_trial_interval=[0.5, 1.0],  # uniform distribution from 0.5–1s
    response_keys=['d', 'k'],      # keys for blue/orange responses
    low_coherence=None,            # will be dynamically updated
    high_coherence=None,
    low_distance=None,
    high_distance=None,
    bonus_factor=0.01               # multiply by number of correct trials
)

###################################
# LOAD CALIBRATION DATA
###################################
def load_calibration_data(participant_number):
    calibration_dir = os.path.join(os.getcwd(), "calibration_data")
    file_prefix = f"{participant_number}_"
    for file_name in os.listdir(calibration_dir):
        if file_name.startswith(file_prefix) and file_name.endswith(".csv"):
            file_path = os.path.join(calibration_dir, file_name)
            break
    else:
        raise FileNotFoundError(
            f"No calibration file found for participant {participant_number} in {calibration_dir}"
        )

    df = pd.read_csv(file_path)
    required_columns = ['low_coherence', 'high_coherence', 'low_distance', 'high_distance']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(
            f"Calibration file for participant {participant_number} is missing required columns: {required_columns}"
        )

    return {
        'low_coherence': df.loc[0, 'low_coherence'],
        'high_coherence': df.loc[0, 'high_coherence'],
        'low_distance': df.loc[0, 'low_distance'],
        'high_distance': df.loc[0, 'high_distance']
    }

participant_number = expInfo['participant nr']
calibration_data = load_calibration_data(participant_number)
gv['low_coherence'] = calibration_data['low_coherence']
gv['high_coherence'] = calibration_data['high_coherence']
gv['low_distance'] = calibration_data['low_distance']
gv['high_distance'] = calibration_data['high_distance']

###################################
# DATA SAVING
###################################
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
    coherence=None,
    coherence_level=None,
    distance=None,
    distance_level=None,

    direction=None,
    reference=None,
    signal_delay=None,

    correct_response=None,        # 'CW' or 'CCW'
    participant_response=None,    # 'CW' or 'CCW'
    correct=None,                 # True/False
    correct_response_colour=None,
    participant_response_colour=None,

    response_time=None,
    confidence_rating=None,
    confidence_response_time=None,

    bonus_payment=None,

    # ------------------------------
    # Staircase parameters
    # ------------------------------
    n_blocks=8,            # number of alternating calibration blocks
    n_trials_per_block=30, # 8 blocks * 30 = 240 trials total
    medium_coherence=0.3,  # initial guess for "medium" coherence
    medium_distance=20,    # initial guess for "medium" distance
    coherence_step=0.01,   # staircase step size for coherence
    distance_step=1,       # staircase step size for distance
)

log_vars = list(info.keys())
if not os.path.exists('calibration_data'):
    os.mkdir('calibration_data')
filename = os.path.join('calibration_data', f"{info['participant']}_{info['session_nr']}_{info['date']}")
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
    fullscr=False,
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
    confidence_response_made=8,
    experiment_end=9
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
    font='Monospace'
)
instructions_txt = visual.TextStim(
    win=win,
    text="\n\n\n\n\n\n Press SPACE to start.",
    height=1,
    pos=[0, 2],
    wrapWidth=30,
    color='white',
    font='Monospace'
)
instructions_top_txt = visual.TextStim(
    win=win,
    text="Instructions",
    height=1,
    pos=[0, 7.5],
    wrapWidth=30,
    color='white',
    font='Monospace'
)

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

###################################
# INSTRUCTIONS
###################################
instructions_txt.text = (
    "You have completed the training session! Now, it will become more difficult to estimate the net direction "
    "of dot motion. It is meant to be difficult, so please do not worry if you find it hard.\n\n"
    f"There will be {info['n_blocks']*info['n_trials_per_block']} trials in total.\n\n\n\n"
    "Press SPACE to continue."
)
instructions_txt.draw()
win.flip()
hf.exit_q(win)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

###################################
# TASK WITH 2-DOWN-1-UP
###################################
EEG_config.send_trigger(EEG_config.triggers['experiment_start'])
start_time = datetime.now()
info['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")

correct_responses = 0
correct_count = 0  # for 2-down-1-up
is_coherence_block = False  # Will flip to True at first block

trial_overall_count = 0

for block_i in range(info['n_blocks']):
    # Alternate between calibrating coherence and distance
    is_coherence_block = not is_coherence_block
    block_type = 'coherence' if is_coherence_block else 'distance'
    print(f"\n=== Starting Block {block_i+1}/{info['n_blocks']} ({block_type} calibration) ===")

    for trial_in_block in range(info['n_trials_per_block']):
        trial_overall_count += 1
        EEG_config.send_trigger(EEG_config.triggers['trial_start'])

        # =========================
        # Choose coherence, distance
        # =========================
        if is_coherence_block:
            # For coherence blocks, use the "medium" values
            coherence_val = info['medium_coherence']
            distance_val = info['medium_distance']
            # Label them as "medium"
            coherence_level = "medium"
            distance_level = "medium"
        else:
            # For distance blocks, pick low or high distance
            if np.random.choice([True, False]):
                distance_val = info['high_distance']
                distance_level = "high"
            else:
                distance_val = info['low_distance']
                distance_level = "low"

            # Then pick coherence accordingly
            # If distance == low_distance => coherence = high_coherence
            # If distance == high_distance => coherence = low_coherence
            if distance_val == info['low_distance']:
                coherence_val = info['high_coherence']
                coherence_level = "high"
            else:
                coherence_val = info['low_coherence']
                coherence_level = "low"

        # =========================
        # Random motion direction & signal delay
        # =========================
        direction = round(np.random.uniform(1, 360), 0)
        signal_delay = np.random.uniform(0.3, 0.8)

        # =========================
        # Reference direction (CW or CCW)
        # =========================
        if np.random.choice([True, False]):
            reference_direction = 'CW'
            reference_angle = (direction + distance_val) % 360
        else:
            reference_direction = 'CCW'
            reference_angle = (direction - distance_val) % 360

        print(
            f"Trial {trial_overall_count}: block={block_i+1}, block_type={block_type}, "
            f"direction={direction}, coherence={coherence_val:.3f}({coherence_level}), "
            f"distance={distance_val:.3f}({distance_level}), reference={reference_angle:.3f}"
        )

        # =========================
        # 1) Fixation
        # =========================
        stimuli = [aperture_outline, fixation]
        delay_time = np.random.uniform(gv['inter_trial_interval'][0], gv['inter_trial_interval'][1])
        hf.draw_all_stimuli(win, stimuli, delay_time)
        hf.exit_q(win)

        # =========================
        # 2) Show dots
        # =========================
        EEG_config.send_trigger(EEG_config.triggers['dots_onset'])
        create_dot_motion_stimulus_n_sets(
            win, frame_rate, direction, coherence_val, signal_delay, dot_parameters, EEG_config
        )

        # =========================
        # 3) Show reference direction
        # =========================
        # Arc colors: We'll do the same logic you used before
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
        stimuli = [aperture_outline, arc_CW, arc_CCW, ref_line, fixation]
        EEG_config.send_trigger(EEG_config.triggers['reference_onset'])
        hf.draw_all_stimuli(win, stimuli)
        hf.exit_q(win)

        # =========================
        # 4) Response
        # =========================
        response_key, response_time = hf.check_key_press(win, gv['response_keys'])
        EEG_config.send_trigger(EEG_config.triggers['response_made'])

        # Map participant's key press to 'CW' or 'CCW' depending on which arc is chosen
        # Same approach: if reference_angle < 180 => top half => left key = CCW, right key = CW, etc.
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
            # 2-down-1-up: Decrease "medium" variable after two consecutive correct trials
            if correct_count == 2:
                correct_count = 0
                if is_coherence_block:
                    # Decrease medium_coherence
                    info['medium_coherence'] = max(info['medium_coherence'] - info['coherence_step'], 0.01)
                else:
                    info['medium_distance'] = max(info['medium_distance'] - info['distance_step'], 1)
        else:
            # Incorrect => reset correct_count, increase medium variable
            correct_count = 0
            if is_coherence_block:
                info['medium_coherence'] = min(info['medium_coherence'] + info['coherence_step'], 1)
            else:
                info['medium_distance'] = min(info['medium_distance'] + info['distance_step'], 50)

        # Update low/high after each trial
        info['low_coherence']  = info['medium_coherence'] * 0.5
        info['high_coherence'] = info['medium_coherence'] * 2.0
        info['low_distance']   = info['medium_distance'] * 0.5
        info['high_distance']  = info['medium_distance'] * 2.0

        # Determine correct color (for logging)
        if reference_direction == 'CW':
            correct_color = arc_CW_color
        else:
            correct_color = arc_CCW_color

        # =========================
        # 5) Optional feedback
        # =========================
        # If you truly don't want participants to get any feedback color, skip this step
        # Otherwise, e.g., show a color for half a second
        stimuli = [aperture_outline, fixation]
        hf.draw_all_stimuli(win, stimuli, 0.5)
        hf.exit_q(win)

        # =========================
        # 6) Confidence rating?
        # (Currently disabled, as you mention "does not include confidence ratings")
        # =========================
        confidence_rating = None
        confidence_response_time = None

        # 7) Clear & wait
        fixation.color = 'white'
        win.flip()
        hf.exit_q(win)
        core.wait(1)

        # =========================
        # 8) SAVE DATA for this trial
        # =========================
        info['trial_count'] = trial_overall_count

        info['coherence']         = coherence_val
        info['coherence_level']   = coherence_level
        info['distance']          = distance_val
        info['distance_level']    = distance_level
        info['direction']         = direction
        info['reference']         = reference_angle
        info['signal_delay']      = signal_delay

        info['correct_response']  = reference_direction   # 'CW'/'CCW'
        info['participant_response'] = chosen_direction   # 'CW'/'CCW'
        info['correct']           = is_correct
        info['correct_response_colour']   = correct_color
        info['participant_response_colour'] = participant_color

        info['response_time']     = response_time
        info['confidence_rating'] = confidence_rating
        info['confidence_response_time'] = confidence_response_time

        # Track current block type if you like
        info['block_type'] = block_type

        datafile.write(','.join(str(info[var]) for var in log_vars) + '\n')
        datafile.flush()

# End of all blocks/trials
EEG_config.send_trigger(EEG_config.triggers['experiment_end'])
end_time = datetime.now()
info['end_time'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
duration = end_time - start_time
info['duration'] = str(duration)

instructions_txt.text = (
    "Well done! You have completed the task.\n\n"
)
instructions_txt.draw()
win.flip()
hf.exit_q(win)
keys = event.waitKeys(keyList=['space'], maxWait=10)
event.clearEvents()

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

win.close()
core.quit()

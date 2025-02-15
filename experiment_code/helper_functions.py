"""
helper functions for main.py, training.py and calibration.py

Maja Friedemann 2025
"""

###################################
# IMPORT PACKAGES
###################################
import random
import time
from psychopy import gui, visual, core, data, event
from psychopy.hardware import keyboard
import pandas as pd
import numpy as np
import serial


###################################
# CLASSES
###################################
class EEGConfig:
    def __init__(self, triggers, send_triggers):
        self.triggers = triggers
        self.send_triggers = send_triggers
        if self.send_triggers:
            # Initialize the serial port connection if send_triggers is True
            self.IOport = serial.Serial('COM6', 115200, timeout=0.001)  # Change port if necessary

    def send_trigger(self, code):
        if self.send_triggers:
            # Actual sending of the trigger over serial port
            try:
                # Send the 'mh' prefix followed by the trigger code and 0 (similar to MATLAB)
                self.IOport.write(b'mh')  # Send 'mh' as two bytes (0x6D, 0x68)
                self.IOport.write(bytes([code, 0]))  # Send trigger code and 0
                self.IOport.flush()

                # Pause briefly (optional, matching MATLAB's pause)
                time.sleep(0.02)

                # Reset the trigger by sending 'mh' followed by 0, 0
                self.IOport.write(b'mh')
                self.IOport.write(bytes([0, 0]))  # Reset to 0
                self.IOport.flush()

                print(f"Trigger {code} sent and reset over serial port.")
            except Exception as e:
                print(f"Failed to send trigger {code} over serial port: {str(e)}")
        else:
            # If send_triggers is False, just print the trigger
            print(f'would send trigger: {code}')


###################################
# FUNCTIONS
###################################
def exit_q(win, key_list=None):
    """
    allow exiting the experiment by pressing q when we are in full screen mode
    this just checks if anything has been pressed - it doesn't wait
    """
    if key_list is None:
        key_list = ['q']
    keys = event.getKeys(keyList=key_list)
    res = len(keys) > 0
    if res:
        if 'q' in keys:
            win.close()
            core.quit()
    event.clearEvents()
    return res


def draw_all_stimuli(win, stimuli, wait=0.01):
    """
    draw all stimuli, flip window, wait (default wait time is 0.01)
    """
    flattened_stimuli = [stim for sublist in stimuli for stim in (sublist if isinstance(sublist, list) else [sublist])]  # flatten the list of stimuli to accommodate nested lists
    for stimulus in flattened_stimuli:
        stimulus.draw()
    win.flip(), exit_q(win), core.wait(wait)


def check_button(win, buttons, stimuli, mouse):
    """
    Check for button hover and click for multiple buttons.
    Return the button object that was clicked and the response time.
    """
    draw_all_stimuli(win, stimuli, 0.2)
    response_timer = core.Clock()  # Start the response timer
    button_glows = [visual.Rect(win, width=button.width+15, height=button.height+15, pos=button.pos, fillColor=button.fillColor, opacity=0.5) for button in buttons]

    while True:  # Use an infinite loop that will break when a button is clicked
        for button, button_glow in zip(buttons, button_glows):
            if button.contains(mouse):  # check for hover
                button_glow.draw()  # hover, draw button glow
            if mouse.isPressedIn(button):  # check for click
                response_time = response_timer.getTime()  # Get the response time
                core.wait(0.5)  # add delay to provide feedback of a click
                return button, response_time  # return the button that was clicked and the response time

        draw_all_stimuli(win, stimuli)  # redraw stimuli and check again


def check_mouse_click(win, mouse):
    mouse.clickReset()
    while True:
        buttons, times = mouse.getPressed(getTime=True)
        if buttons[0]:
            return 'left', times[0]
        if buttons[2]:
            return 'right', times[2]
        exit_q(win)
        core.wait(0.01)


def check_key_press(win, key_list):
    while True:
        keys = event.getKeys(timeStamped=True)
        for key, time in keys:
            if key in key_list:
                return key, time
        exit_q(win)
        event.clearEvents()
        core.wait(0.01)


def convert_rgb_to_psychopy(rgb):
    """
    turn rgp colour code to colour format that PsychoPy needs
    """
    return tuple([(x / 127.5) - 1 for x in rgb])


def draw_arc(win, radius, start_deg, end_deg, color, pos=(0, 0)):
    num_segments = 100
    angles = np.linspace(np.deg2rad(start_deg), np.deg2rad(end_deg), num_segments)
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    vertices = np.column_stack([x, y])
    return visual.ShapeStim(win, vertices=vertices, closeShape=False, lineColor=color, pos=pos, lineWidth=6)


# def get_confidence_rating(win, gv, EEG_config=None):
#     """
#     Displays a confidence rating Slider and allows press-and-hold movement
#     for left/right keys. The participant MUST move the slider at least once
#     before 'space' can confirm and end the rating.
#
#     Returns:
#       (final_rating, response_time, confidence_start, adjustments_serialized)
#
#     Times are rounded to 4 decimals.
#     """
#
#     left_key, right_key = gv['response_keys']
#     confirm_key = 'space'
#
#     kb = keyboard.Keyboard()  # A single Keyboard object for event capture
#
#     # Prepare slider labels: positions 0..10 → 50..100%
#     slider_labels = [50 + i * 5 for i in range(11)]
#
#     # Create the slider
#     slider = visual.Slider(
#         win=win,
#         ticks=list(range(11)),  # 11 steps
#         labels=None,
#         pos=(0, 0),
#         size=(15, 2),
#         units="deg",
#         flip=True,
#         style=['slider'],
#         granularity=1,
#         markerColor='green',
#         font='Arial',
#     )
#     slider.marker.setSize((0.6, 2))
#
#     # Create label texts
#     label_50 = visual.TextStim(win=win, text="50%", height=0.8, pos=(-9, 0), color='white')
#     label_100 = visual.TextStim(win=win, text="100%", height=0.8, pos=(9, 0), color='white')
#
#     # Random initial position
#     initial_pos = random.choice(slider.ticks)
#     slider.markerPos = initial_pos
#     confidence_start = slider_labels[initial_pos]
#
#     # Question & numeric text
#     slider_question_text = visual.TextStim(
#         win=win,
#         text='How confident are you in your last response?',
#         height=1,
#         pos=(0, 5),
#         color='white',
#         bold=True,
#         font='Arial',
#         alignText='center',
#         wrapWidth=30
#     )
#     slider_rating_txt = visual.TextStim(
#         win=win,
#         text=f"{confidence_start}%",
#         height=0.8,
#         pos=(0, 2),
#         color='white',
#         font='Arial',
#     )
#
#     # Record timing & initial adjustment
#     start_time = time.time()
#     adjustments = [(confidence_start, 0.0)]  # (confidence_value, seconds_from_start)
#
#     if EEG_config is not None:
#         EEG_config.send_trigger(EEG_config.triggers['confidence_rating_onset'])
#
#     kb.clearEvents()
#
#     # We'll keep track of which keys are currently held down
#     keys_held = set()
#
#     # Track if the slider has *ever* moved at least once
#     slider_moved = False
#
#     # Time-based gating to control how fast the marker moves while held
#     move_interval = 0.15  # seconds between steps while holding
#     last_move_time = 0
#
#     break_loop = False
#
#     while not break_loop:
#         # 1) Get all key events that happened since the last frame
#         key_events = kb.getKeys(keyList=[left_key, right_key, confirm_key],
#                                 waitRelease=False, clear=False)
#
#         for evt in key_events:
#             # If user pressed space, that might be our confirmation
#             if evt.name == confirm_key:
#                 # Only confirm if the slider was moved at least once
#                 if evt.duration is None and slider_moved:
#                     # user has pressed space => confirm
#                     if EEG_config is not None:
#                         EEG_config.send_trigger(EEG_config.triggers['confidence_response_made'])
#                     slider.markerColor = 'darkgreen'
#                     slider_rating_txt.color = 'darkgreen'
#                     break_loop = True
#                     break
#                 # If slider wasn't moved yet, ignore this press
#
#             # If user pressed or released left_key
#             elif evt.name == left_key:
#                 if evt.duration is None:
#                     # Key down event => track in keys_held
#                     keys_held.add(left_key)
#                 else:
#                     # Key release
#                     if left_key in keys_held:
#                         keys_held.remove(left_key)
#
#             # If user pressed or released right_key
#             elif evt.name == right_key:
#                 if evt.duration is None:
#                     keys_held.add(right_key)
#                 else:
#                     if right_key in keys_held:
#                         keys_held.remove(right_key)
#
#         # 2) Now check if left_key or right_key is currently held
#         now = time.time()
#
#         # Move left if enough time has passed and left_key is held
#         if left_key in keys_held and (now - last_move_time > move_interval):
#             if slider.markerPos > 0:
#                 slider.markerPos -= 1
#                 adj_time = round(now - start_time, 4)
#                 adjustments.append((slider_labels[int(slider.markerPos)], adj_time))
#                 slider_moved = True
#                 if EEG_config is not None:
#                     EEG_config.send_trigger(EEG_config.triggers['confidence_decrease'])
#             last_move_time = now
#
#         # Move right if enough time has passed and right_key is held
#         if right_key in keys_held and (now - last_move_time > move_interval):
#             if slider.markerPos < 10:
#                 slider.markerPos += 1
#                 adj_time = round(now - start_time, 4)
#                 adjustments.append((slider_labels[int(slider.markerPos)], adj_time))
#                 slider_moved = True
#                 if EEG_config is not None:
#                     EEG_config.send_trigger(EEG_config.triggers['confidence_increase'])
#             last_move_time = now
#
#         # 3) Update displayed rating, draw, flip
#         slider_rating_txt.text = f"{slider_labels[int(slider.markerPos)]}%"
#         slider.draw()
#         label_50.draw()
#         label_100.draw()
#         slider_rating_txt.draw()
#         slider_question_text.draw()
#         win.flip()
#
#     # Done collecting response
#     # Round the final response_time to 4 decimals
#     response_time = round(time.time() - start_time, 4)
#     final_rating = slider_labels[int(slider.markerPos)]
#
#     # Serialize adjustments (times are already rounded above)
#     steps = [str(adj[0]) for adj in adjustments]
#     times = [str(adj[1]) for adj in adjustments]
#     adjustments_serialized = {
#         "step_list": '|'.join(steps),
#         "time_list": '|'.join(times)
#     }
#
#     core.wait(0.7)
#     return final_rating, response_time, confidence_start, adjustments_serialized
#


def get_confidence_rating(win, gv, EEG_config=None):
    left_key, right_key = gv['response_keys']
    confirm_key = 'space'

    kb = keyboard.Keyboard()
    slider_labels = [50 + i * 5 for i in range(11)]

    slider = visual.Slider(
        win=win,
        ticks=list(range(11)),
        labels=None,
        pos=(0, 0),
        size=(15, 2),
        units="deg",
        flip=True,
        style=['slider'],
        granularity=1,
        markerColor='green',
        font='Arial',
    )
    slider.marker.setSize((0.6, 2))

    label_50 = visual.TextStim(win=win, text="50%", height=0.8, pos=(-9, 0), color='white')
    label_100 = visual.TextStim(win=win, text="100%", height=0.8, pos=(9, 0), color='white')

    # Ensure the random starting position is within the middle half (positions 3, 4, 5, 6, 7)
    initial_pos = random.choice(range(3, 8))  # Picks from 3, 4, 5, 6, 7 (avoids 0, 1, 2, 8, 9, 10)
    slider.markerPos = initial_pos
    confidence_start = slider_labels[initial_pos]

    slider_question_text = visual.TextStim(
        win=win,
        text='How confident are you in your last response?',
        height=1,
        pos=(0, 5),
        color='white',
        bold=True,
        font='Arial',
        alignText='center',
        wrapWidth=30
    )
    slider_rating_txt = visual.TextStim(
        win=win,
        text=f"{confidence_start}%",
        height=0.8,
        pos=(0, 2),
        color='white',
        font='Arial',
    )

    start_time = time.time()
    adjustments = [(confidence_start, 0.0)]
    slider_moved = False

    if EEG_config is not None:
        EEG_config.send_trigger(EEG_config.triggers['confidence_rating_onset'])

    kb.clearEvents()

    while True:
        key_events = kb.getKeys(keyList=[left_key, right_key, confirm_key], waitRelease=False)

        for evt in key_events:
            if evt.name == confirm_key:
                if slider_moved:
                    if EEG_config is not None:
                        EEG_config.send_trigger(EEG_config.triggers['confidence_response_made'])
                    slider.markerColor = 'darkgreen'
                    slider_rating_txt.color = 'darkgreen'
                    break_loop = True
                    break
            elif evt.name == left_key and slider.markerPos > 0:
                slider.markerPos -= 1
                adj_time = round(time.time() - start_time, 4)
                adjustments.append((slider_labels[int(slider.markerPos)], adj_time))
                slider_moved = True
                if EEG_config is not None:
                    EEG_config.send_trigger(EEG_config.triggers['confidence_decrease'])
            elif evt.name == right_key and slider.markerPos < 10:
                slider.markerPos += 1
                adj_time = round(time.time() - start_time, 4)
                adjustments.append((slider_labels[int(slider.markerPos)], adj_time))
                slider_moved = True
                if EEG_config is not None:
                    EEG_config.send_trigger(EEG_config.triggers['confidence_increase'])

        slider_rating_txt.text = f"{slider_labels[int(slider.markerPos)]}%"
        slider.draw()
        label_50.draw()
        label_100.draw()
        slider_rating_txt.draw()
        slider_question_text.draw()
        win.flip()

        if 'break_loop' in locals():
            break

    response_time = round(time.time() - start_time, 4)
    final_rating = slider_labels[int(slider.markerPos)]

    adjustments_serialized = {
        "step_list": '|'.join(str(adj[0]) for adj in adjustments),
        "time_list": '|'.join(str(adj[1]) for adj in adjustments)
    }

    core.wait(0.7)
    return final_rating, response_time, confidence_start, adjustments_serialized

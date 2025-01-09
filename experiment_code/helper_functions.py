"""
helper functions for main.py and staircase.py

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


###################################
# CLASSES
###################################
class EEGConfig:
    def __init__(self, triggers, send_triggers):
        self.triggers = triggers
        self.send_triggers = send_triggers

    def send_trigger(self, code):
        if self.send_triggers:
            print('write function to trigger code ' + str(code))
        else:
            print('would send trigger: ' + str(code))


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


def get_confidence_rating(win, gv, EEG_config=None):
    """
    Displays a confidence rating Slider, controlled by left/right keys from `gv['response_keys']`
    and 'space' to confirm. Returns rating (50–100) and response time.
    The slider marker color changes upon space press.
    """

    kb = keyboard.Keyboard()  # Use modern Keyboard class

    # Slider labels (positions 0–5 → 50%, 60%, 70%, 80%, 90%, 100%)
    slider_labels = ["50%", "60%", "70%", "80%", "90%", "100%"]

    # Create the Slider
    # - style includes 'triangleMarker' to give a more noticeable triangular marker
    # - remove markerSize, as older PsychoPy doesn't support it
    slider = visual.Slider(
        win=win,
        ticks=[0, 1, 2, 3, 4, 5],
        labels=["50%", "", "", "", "", "100%"],  # optional
        pos=(0, 0),
        size=(15, 2),
        units="deg",
        flip=True,
        style=['slider'],
        granularity=1,
        labelHeight=0.7,
        markerColor='green'
    )
    slider.marker.setSize((0.6, 2))

    # Random initial position
    initial_pos = random.choice(slider.ticks)
    slider.markerPos = initial_pos

    # Question prompt
    slider_question_text = visual.TextStim(
        win=win,
        text='How confident are you?',
        height=1,
        pos=(0, 5),
        color='white',
        bold=True,
        font='Arial',
        alignText='center',
        wrapWidth=30
    )

    # TextStim to display numeric/percentage feedback
    slider_rating_txt = visual.TextStim(
        win=win,
        text=slider_labels[initial_pos],
        height=0.7,
        pos=(0, -1.65),
        color='white'
    )

    # Record the start time
    start_time = time.time()

    break_loop = False
    while not break_loop:
        # Poll keyboard for relevant keys
        keys = kb.getKeys(keyList=gv['response_keys'] + ['space'], waitRelease=False)

        for key in keys:
            if key.name == gv['response_keys'][0]:  # e.g. 'left'
                slider.markerPos = max(slider.markerPos - 1, 0)
            elif key.name == gv['response_keys'][1]:  # e.g. 'right'
                slider.markerPos = min(slider.markerPos + 1, 5)
            elif key.name == 'space':
                if EEG_config is not None:
                    EEG_config.send_trigger(EEG_config.triggers['confidence_response_made'])
                # Change marker color upon confirmation
                slider.markerColor = 'black'
                break_loop = True

        # Update the rating text to match current marker position
        slider_rating_txt.text = slider_labels[int(slider.markerPos)]

        # Draw all stimuli
        slider.draw()
        slider_rating_txt.draw()
        slider_question_text.draw()
        win.flip()  # sync to screen refresh

    # Record end time
    end_time = time.time()
    response_time = end_time - start_time

    # Convert marker position to confidence rating (50 + markerPos * 10)
    rating = 50 + slider.markerPos * 10

    # Show the changed marker color briefly before returning
    slider.draw()
    slider_rating_txt.draw()
    slider_question_text.draw()
    win.flip()
    core.wait(0.5)

    return rating, response_time


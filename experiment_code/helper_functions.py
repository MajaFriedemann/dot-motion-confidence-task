"""
helper functions for main.py and staircase.py

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import random
import time
from psychopy import gui, visual, core, data, event
import pandas as pd
import numpy as np
from RDK_3_sets_psychopy import DotStimMN


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


def create_dot_motion_stimulus(win, dot_params, motion_direction, motion_coherence):
    """
    create dot motion stimulus with specified direction and coherence
    this just uses the dotStim from psychopy
    """
    return visual.DotStim(
        win=win,
        dir=motion_direction,
        coherence=motion_coherence,
        **dot_params
    )


def draw_arc(win, radius, start_deg, end_deg, color, pos=(0, 0)):
    num_segments = 100
    angles = np.linspace(np.deg2rad(start_deg), np.deg2rad(end_deg), num_segments)
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    vertices = np.column_stack([x, y])
    return visual.ShapeStim(win, vertices=vertices, closeShape=False, lineColor=color, pos=pos, lineWidth=6)


def get_confidence_rating(win, gv):
    """
    Confidence rating with response time
    """
    slider = visual.Slider(win,
                           ticks=[0, 1, 2, 3, 4, 5],
                           labels=["50%", "", "", "", "", "100%"],
                           pos=(0, 0),
                           size=(15, 2), units="deg", flip=True, style='slider', granularity=1, labelHeight=0.7)
    slider.tickLines.sizes = (0.1, 2)
    initial_pos = random.choice(slider.ticks)  # generate a random initial position for the slider marker
    slider.markerPos = initial_pos  # set the slider marker to the initial random position
    slider_marker = visual.ShapeStim(
        win=win,
        vertices=((-0.2, -1), (0.2, -1), (0.2, 1), (-0.2, 1)),
        lineWidth=2,
        pos=(slider.markerPos * (slider.size[0] / 5) - (slider.size[0] / 2), slider.pos[1]),
        closeShape=True,
        fillColor='green',
        lineColor='green'
    )
    slider_labels = ["50%", "60%", "70%", "80%", "90%", "100%"]
    slider_rating_txt = visual.TextStim(win=win, text=slider_labels[initial_pos], height=0.6,
                                        pos=(slider_marker.pos[0], -1.65), color='white')
    slider_question_text = visual.TextStim(
        win,
        text=f'How confident are you?',
        height=1,
        pos=(0, 5),
        color='white',
        bold=True,
        font='Arial',
        alignText='center',
        wrapWidth=30
    )

    start_time = time.time()  # Record the start time

    while True:
        keys = event.getKeys()
        if gv['response_keys'][0] in keys:
            slider.markerPos = max(slider.markerPos - 1, 0)
        elif gv['response_keys'][1] in keys:
            slider.markerPos = min(slider.markerPos + 1, 5)
        elif 'space' in keys:
            break
        slider_marker.pos = (slider.markerPos * (slider.size[0] / 5) - (slider.size[0] / 2), slider.pos[1])
        slider_rating_txt.pos = (slider_marker.pos[0], slider.pos[1] - 1.65)
        slider_rating_txt.text = slider_labels[int(slider.markerPos)]
        stimuli = [slider, slider_rating_txt, slider_question_text, slider_marker]
        draw_all_stimuli(win, stimuli)

    end_time = time.time()  # Record the end time
    response_time = end_time - start_time  # Calculate the response time

    rating = 50 + slider.markerPos * 10  # convert the marker position to the percentage rating
    slider_marker.lineColor = 'black'
    slider_marker.fillColor = 'black'
    draw_all_stimuli(win, stimuli, 0.5)

    return rating, response_time  # Return both the rating and the response time


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


def get_confidence_rating(win, gv, EEG_config=None):
    """
    Displays a confidence rating Slider, controlled by left/right keys from `gv['response_keys']`
    and 'space' to confirm. Returns rating (50–100), response time, initial position,
    and a list of adjustments made.
    """

    kb = keyboard.Keyboard()  # Use modern Keyboard class

    # Slider labels (positions 0–9 → 50%, 55%, ..., 100%)
    slider_labels = [50 + i * 5 for i in range(10)]  # Actual confidence values

    # Create the Slider
    slider = visual.Slider(
        win=win,
        ticks=list(range(10)),  # 10 steps from 0 to 9
        labels=None,  # Disable built-in labels
        pos=(0, 0),  # Position of the slider
        size=(15, 2),  # Width and height of the slider
        units="deg",
        flip=True,
        style=['slider'],
        granularity=1,
        markerColor='green',
        font='Arial',
    )

    slider.marker.setSize((0.6, 2))  # Adjust marker size

    # Create Separate Labels
    label_50 = visual.TextStim(
        win=win,
        text="50%",  # Left label
        height=0.8,  # Font size
        pos=(-9, 0),  # Position: left of the slider
        color='white',
        font='Arial',
    )

    label_100 = visual.TextStim(
        win=win,
        text="100%",  # Right label
        height=0.8,  # Font size
        pos=(9, 0),  # Position: right of the slider
        color='white',
        font='Arial',
    )

    # Random initial position
    initial_pos = random.choice(slider.ticks)
    slider.markerPos = initial_pos

    # Convert the initial position to a confidence percentage
    confidence_start = slider_labels[initial_pos]

    # Question prompt
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

    # TextStim to display numeric/percentage feedback
    slider_rating_txt = visual.TextStim(
        win=win,
        text=f"{confidence_start}%",  # Display confidence value
        height=0.8,
        pos=(0, 2),
        color='white',
        font='Arial',
    )

    # Record the start time and adjustments
    start_time = time.time()
    adjustments = [(confidence_start, 0)]  # Record the initial confidence value and time
    if EEG_config is not None:
        EEG_config.send_trigger(EEG_config.triggers['confidence_rating_onset'])

    kb.clearEvents()
    break_loop = False
    while not break_loop:
        # Poll keyboard for relevant keys
        keys = kb.getKeys(keyList=gv['response_keys'] + ['space'], waitRelease=False)

        for key in keys:
            if key.name == gv['response_keys'][0]:  # e.g., 'left'
                if slider.markerPos > 0:
                    slider.markerPos -= 1
                    adjustment_time = time.time() - start_time
                    adjustments.append((slider_labels[int(slider.markerPos)], adjustment_time))
                    if EEG_config is not None:
                        EEG_config.send_trigger(EEG_config.triggers['confidence_decrease'])
            elif key.name == gv['response_keys'][1]:  # e.g., 'right'
                if slider.markerPos < 9:  # Adjusted for 10 steps
                    slider.markerPos += 1
                    adjustment_time = time.time() - start_time
                    adjustments.append((slider_labels[int(slider.markerPos)], adjustment_time))
                    if EEG_config is not None:
                        EEG_config.send_trigger(EEG_config.triggers['confidence_increase'])
            elif key.name == 'space':
                if EEG_config is not None:
                    EEG_config.send_trigger(EEG_config.triggers['confidence_response_made'])
                # Change marker color upon confirmation
                slider.markerColor = 'darkgreen'
                slider_rating_txt.color = 'darkgreen'
                break_loop = True

        # Update the rating text to match current marker position
        slider_rating_txt.text = f"{slider_labels[int(slider.markerPos)]}%"

        # Draw all stimuli
        slider.draw()
        label_50.draw()
        label_100.draw()
        slider_rating_txt.draw()
        slider_question_text.draw()
        win.flip()  # sync to screen refresh

    # Record end time
    response_time = time.time() - start_time

    # Final rating value
    final_rating = slider_labels[int(slider.markerPos)]

    # Serialize adjustments for saving
    steps = [str(adj[0]) for adj in adjustments]  # Extract confidence values
    times = [str(adj[1]) for adj in adjustments]  # Extract times
    adjustments_serialized = {
        "step_list": '|'.join(steps),  # Serialize steps with | separator
        "time_list": '|'.join(times)  # Serialize times with | separator
    }
    core.wait(0.7)
    return final_rating, response_time, confidence_start, adjustments_serialized







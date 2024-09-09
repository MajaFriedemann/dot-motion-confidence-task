import numpy as np
from psychopy import visual, core, event, monitors

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


def create_dot_motion_stimulus_3_sets(win, motion_direction, motion_coherence):
    """
    Create a random dot motion stimulus with 3 sets of dots, with the specified motion direction and coherence.

    Parameters:
    - win: the PsychoPy window in which to display the stimulus
    - motion_direction: the direction of coherent motion (in degrees)
    - motion_coherence: the proportion of dots moving in the coherent direction (0.0 to 1.0)
    """
    # Parameters
    aperture_diameter = 8  # Diameter of circular aperture in degrees (updated)
    dot_diameter = 0.12  # Dot diameter in degrees
    fixation_diameter = 0.2  # Fixation cross diameter
    dot_density = 16  # Dot density in dots per degrees^-2 per second (updated)
    speed = 2  # Speed of motion in degrees per second (updated)

    frame_duration = 1.0 / win.getActualFrameRate()  # Adapt to monitor frame rate
    move_distance = speed * frame_duration  # Distance a coherent dot moves in one frame
    n_frames_between_sets = 2  # Number of frames between dot set replots

    # Calculate the number of dots
    aperture_area = np.pi * (aperture_diameter / 2) ** 2  # Area of the aperture in degrees^2
    n_dots = int(dot_density * aperture_area)  # Number of dots based on density

    # Function to generate random dot positions within a circular aperture
    def generate_random_dots(n_dots):
        angles = np.random.rand(n_dots) * 2 * np.pi  # Random angles
        radii = np.sqrt(np.random.rand(n_dots)) * (aperture_diameter / 2)  # Random radii
        x_positions = radii * np.cos(angles)  # Convert polar to cartesian
        y_positions = radii * np.sin(angles)
        return np.column_stack((x_positions, y_positions))

    # Initialize dot positions (for three sets)
    dot_sets = [generate_random_dots(n_dots) for _ in range(3)]

    # Convert motion direction to radians
    motion_direction_rad = np.deg2rad(motion_direction)

    # Initialize fixation cross
    fixation = visual.Circle(win, radius=fixation_diameter / 2, fillColor='white', lineColor='white')

    # Create dot stimuli
    dot_stim = visual.ElementArrayStim(
        win, nElements=n_dots, sizes=dot_diameter,
        elementTex=None, elementMask='circle', units='deg'
    )

    # Pre-define coherent and random dot indices
    coherent_indices = np.random.choice(n_dots, int(n_dots * motion_coherence), replace=False)
    random_indices = np.setdiff1d(np.arange(n_dots), coherent_indices)

    def update_dots(dot_positions):
        """
        Update the positions of the dots based on pre-defined coherent and random dot sets.
        """
        # Update coherent dots
        dot_positions[coherent_indices, 0] += np.cos(motion_direction_rad) * move_distance
        dot_positions[coherent_indices, 1] += np.sin(motion_direction_rad) * move_distance

        # Wrap coherent dots that move out of the aperture
        distances_from_center = np.sqrt(dot_positions[:, 0] ** 2 + dot_positions[:, 1] ** 2)
        outside_aperture = distances_from_center > (aperture_diameter / 2)
        dot_positions[outside_aperture] = generate_random_dots(np.sum(outside_aperture))

        # Only randomize dots that move out of bounds
        return dot_positions

    # Set up a clock to control frame timing
    clock = core.Clock()

    # Main loop: present the stimulus until a key is pressed
    frame_count = 0
    while not event.getKeys():
        # Select the appropriate dot set for the current frame
        current_set = frame_count % 3

        # Update dots for the current set
        dot_sets[current_set] = update_dots(dot_sets[current_set])

        # Update the dot stimulus with the current set's positions
        dot_stim.xys = dot_sets[current_set]

        # Draw the fixation cross
        fixation.draw()

        # Draw the dots
        dot_stim.draw()

        # Flip the window buffer
        win.flip()

        # Increment the frame counter
        frame_count += 1

        # Brief pause between frames
        core.wait(frame_duration)

    # Close the window when done
    win.close()


create_dot_motion_stimulus_3_sets(win, motion_direction=180, motion_coherence=0.5)

import numpy as np
from psychopy import visual, core, event, monitors

# Create the window
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
    aperture_diameter = 8  # Diameter of circular aperture in degrees (8 in Bang et al 2020)
    dot_diameter = 0.12  # Dot diameter in degrees (0.12 in Bang et al 2020)
    fixation_diameter = 0.2  # Fixation cross diameter in degrees (0.2 in Bang et al 2020)
    fixation_exclusion_radius = 0.3  # No-dots zone radius around the fixation cross

    dot_density = 16  # Dot density in dots per degrees^-2 per second (16 in Bang et al 2020)
    aperture_area = np.pi * (aperture_diameter / 2) ** 2  # Area of the aperture in degrees^2
    n_dots = int(dot_density * aperture_area)  # Number of dots based on density

    speed = 2  # Speed of motion in degrees per second (2 in Bang et al 2020)
    frame_duration = 1.0 / win.getActualFrameRate()  # Frame rate 60Hz --> 1/60 = 0.0167 seconds
    move_distance = speed * frame_duration  # Distance a coherent dot moves in one frame

    # Generate random dot positions within the circular aperture
    def generate_random_dots(n_dots):
        """
        Generates dots uniformly within a circular aperture without excluding dots near the fixation.
        """
        dots = []
        while len(dots) < n_dots:
            angles = np.random.rand(n_dots) * 2 * np.pi  # Random angles for dot direction
            radii = np.sqrt(np.random.rand(n_dots)) * (aperture_diameter / 2)  # Random radii (for circular area)
            x_positions = radii * np.cos(angles)  # Convert polar to Cartesian coordinates (x)
            y_positions = radii * np.sin(angles)  # Convert polar to Cartesian coordinates (y)
            dots.extend(np.column_stack((x_positions, y_positions)))
        return np.array(dots)  # Return exactly n_dots

    # Generate random dot positions for three sets of dots
    dot_sets = [generate_random_dots(n_dots) for _ in range(3)]

    # Convert motion direction from degrees to radians
    motion_direction_rad = np.deg2rad(motion_direction)

    # Initialize a fixation cross
    fixation = visual.ShapeStim(
        win,
        vertices=[(-fixation_diameter / 2, 0), (fixation_diameter / 2, 0), (0, 0), (0, fixation_diameter / 2),
                  (0, -fixation_diameter / 2)],
        lineWidth=2,
        closeShape=False,
        lineColor='white'
    )

    # Create the dot stimulus
    dot_stim = visual.ElementArrayStim(
        win,
        nElements=n_dots,
        sizes=dot_diameter,
        elementTex=None,
        elementMask='circle',
        units='deg'
    )

    def wrap_around_circular(dot_positions):
        """
        Implement circular wrapping. When a dot leaves one side of the aperture, it re-enters from the other side
        at the same distance and angle, keeping the motion direction consistent.
        """
        # Calculate distance from center for each dot
        distances_from_center = np.sqrt(dot_positions[:, 0] ** 2 + dot_positions[:, 1] ** 2)
        outside_aperture = distances_from_center > (aperture_diameter / 2)

        if np.any(outside_aperture):
            # Move dots that are outside the aperture back into the opposite side of the circle
            dot_positions[outside_aperture, 0] *= -1  # Reflect across the center
            dot_positions[outside_aperture, 1] *= -1  # Reflect across the center

        return dot_positions

    def compute_dot_opacity(dot_positions):
        """
        Set opacity based on whether a dot is in the no-dot zone or outside it.
        Dots inside the no-dot zone will have opacity 0 (invisible), others will have opacity 1 (visible).
        """
        distances_from_center = np.sqrt(dot_positions[:, 0] ** 2 + dot_positions[:, 1] ** 2)
        opacities = np.ones(len(dot_positions))  # Default all opacities to 1 (visible)
        inside_no_dot_zone = distances_from_center < fixation_exclusion_radius
        opacities[inside_no_dot_zone] = 0  # Make dots inside the no-dot zone transparent
        return opacities

    def update_dots(dot_positions):
        """
        Update the positions of the dots and reshuffle the coherent and random assignment each frame.
        """
        # Randomly assign which dots are coherent and which are random for this frame
        coherent_indices = np.random.choice(n_dots, int(n_dots * motion_coherence), replace=False)
        random_indices = np.setdiff1d(np.arange(n_dots), coherent_indices)

        # Update coherent dots (those moving in a specific direction)
        dot_positions[coherent_indices, 0] += np.cos(motion_direction_rad) * move_distance
        dot_positions[coherent_indices, 1] += np.sin(motion_direction_rad) * move_distance

        # Update random dots (those moving in random directions)
        random_angles = np.random.rand(len(random_indices)) * 2 * np.pi  # Random angles for random dots
        dot_positions[random_indices, 0] += np.cos(random_angles) * move_distance  # Move in random x-direction
        dot_positions[random_indices, 1] += np.sin(random_angles) * move_distance  # Move in random y-direction

        # Wrap dots that move outside the aperture (circular wrapping)
        dot_positions = wrap_around_circular(dot_positions)

        # Compute dot opacities (transparent for dots in the no-dot zone, visible otherwise)
        dot_opacity = compute_dot_opacity(dot_positions)

        return dot_positions, dot_opacity

    # Main loop: present the stimulus until a key is pressed
    frame_count = 0
    while not event.getKeys():
        # Select the appropriate dot set for the current frame
        current_set = frame_count % 3

        # Update dots for the current set and get their opacities
        dot_sets[current_set], dot_opacities = update_dots(dot_sets[current_set])

        # Update the dot stimulus with the current set's positions
        dot_stim.xys = dot_sets[current_set]  # Update dot positions
        dot_stim.opacities = dot_opacities  # Update opacities based on their location

        # Draw the fixation cross
        fixation.draw()

        # Draw the dots
        dot_stim.draw()

        # Flip the window buffer to show the updated frame
        win.flip()

        # Increment the frame counter
        frame_count += 1

        # Brief pause between frames
        core.wait(frame_duration)

    # Close the window when done
    win.close()


create_dot_motion_stimulus_3_sets(win, motion_direction=180, motion_coherence=0.5)

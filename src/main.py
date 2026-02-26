import pygame
from display import (Window, TextBox, SlideBox, DropdownBox, ButtonBox,
                     CounterBox, ModeButtonBox, LabelBox,
                     ToggleButtonBox, LeaderboardTable, StepButtonBox)
from algs import algorithmsDict
from counters import reset_counters, get_comparisons, get_swaps, set_current_instance
from database import save_record, get_records, get_algorithms, export_csv
import os
from random import randint
import time
import math
import copy

# Initialize pygame modules
pygame.init()

# Font
baseFont = pygame.font.SysFont('Arial', 24)
smallFont = pygame.font.SysFont('Arial', 18)
titleFont = pygame.font.SysFont('Arial', 36, bold=True)

# Colors
grey = (100, 100, 100)
green = (125, 240, 125)
white = (250, 250, 250)
red = (255, 50, 50)
black = (0, 0, 0)
blue = (50, 50, 255)
dark_blue = (30, 30, 120)
light_grey = (200, 200, 200)
arena_color = (255, 100, 100)
solo_color = (100, 150, 255)

# Additional font for leaderboard table
tinyFont = pygame.font.SysFont('Arial', 14)

# ── Solo-mode visualization geometry ────────────────────────────────────────
# A 45 px control strip occupies the far-left of the screen.
# All bar drawing is offset to start at x=45 and uses the remaining width.
VIZ_X_OFFSET  = 45    # left edge of the bar area
VIZ_WIDTH     = 855   # width available for bars  (900 - VIZ_X_OFFSET)
VIZ_MAX_H     = 400   # maximum bar height (pixels)
VIZ_Y_OFFSET  = 0     # top of bar area

# Maximum number of snapshots kept in the step-back history.
# Each snapshot stores two small lists (array + heat) → ~1 KB for 200 bars.
HISTORY_LIMIT = 500

# Game modes
MODE_SELECTION = 0
SOLO_MODE = 1
ARENA_MODE = 2
LEADERBOARD_MODE = 3

pygame.display.set_caption('Sorting Algorithms Visualizer')
screen = pygame.display.set_mode((900, 500))

# Global state
game_mode = MODE_SELECTION
solo_window = None
arena_window = None

def init_solo_mode():
    """Initialize the solo mode window and widgets."""
    window = Window(screen)

    # ── Bottom control bar ───────────────────────────────────────────────────
    window.add_widget(
        widget_id='size_input',
        widget=TextBox((30, 440, 100, 50), 'Size', grey, baseFont, '100')
    )
    window.add_widget(
        widget_id='delay_slider',
        widget=SlideBox((140, 440, 150, 50), 'Delay', grey, baseFont)
    )
    window.add_widget(
        widget_id='algorithm_input',
        widget=DropdownBox((300, 440, 200, 50), 'Algorithm', grey, baseFont,
                           list(algorithmsDict.keys()), white)
    )
    window.add_widget(
        widget_id='play_button',
        widget=ButtonBox((510, 445, 40, 40), 'res/playButton.png', 'res/stopButton.png')
    )
    window.add_widget(
        widget_id='comparisons_counter',
        widget=CounterBox((570, 440, 100, 50), 'Comparisons', grey, baseFont)
    )
    window.add_widget(
        widget_id='swaps_counter',
        widget=CounterBox((690, 440, 100, 50), 'Swaps', grey, baseFont)
    )
    window.add_widget(
        widget_id='elapsed_counter',
        widget=CounterBox((810, 440, 80, 50), 'Time(s)', grey, baseFont)
    )

    # ── Left-side playback controls (x=2, centred vertically in viz area) ───
    # Step-back  ◀  (also triggered by LEFT arrow key)
    window.add_widget(
        'step_back_label',
        LabelBox((2, 145, 40, 15), 'Prev', grey, tinyFont)
    )
    window.add_widget(
        widget_id='step_back_btn',
        widget=StepButtonBox((2, 160, 40, 40), '◀', baseFont)
    )
    # Pause / Resume toggle  ⏸ / ▶
    window.add_widget(
        'pause_label',
        LabelBox((2, 205, 40, 15), 'Pause', grey, tinyFont)
    )
    window.add_widget(
        widget_id='pause_btn',
        widget=ToggleButtonBox((2, 220, 40, 40), '⏸', baseFont,
                               color_off=(80, 80, 80), color_on=(50, 150, 80))
    )
    # Step-forward  ▶  (also triggered by RIGHT arrow key)
    window.add_widget(
        'step_fwd_label',
        LabelBox((2, 265, 40, 15), 'Next', grey, tinyFont)
    )
    window.add_widget(
        widget_id='step_fwd_btn',
        widget=StepButtonBox((2, 280, 40, 40), '▶', baseFont)
    )

    # ── Navigation ──────────────────────────────────────────────────────────
    window.add_widget(
        widget_id='back_button',
        widget=LabelBox((820, 10, 70, 30), 'Back', white, smallFont, grey)
    )

    return window

def init_arena_mode():
    """Initialize the arena mode window and widgets."""
    window = Window(screen)
    
    # Top controls - Size, Play, Back
    window.add_widget(
        widget_id='size_input',
        widget=TextBox((50, 10, 80, 40), 'Size', grey, smallFont, '50')
    )
    window.add_widget(
        widget_id='play_button',
        widget=ButtonBox((150, 10, 40, 40), 'res/playButton.png', 'res/stopButton.png')
    )
    window.add_widget(
        widget_id='back_button',
        widget=LabelBox((820, 10, 70, 30), 'Back', white, smallFont, grey)
    )
    
    # Winner label (centered top)
    window.add_widget(
        widget_id='winner_label',
        widget=LabelBox((300, 10, 300, 40), '', arena_color, baseFont)
    )
    
    # Left competitor counters (below visualization)
    window.add_widget(
        widget_id='algo1_comparisons',
        widget=CounterBox((50, 380, 80, 35), 'Comp', grey, smallFont)
    )
    window.add_widget(
        widget_id='algo1_swaps',
        widget=CounterBox((140, 380, 80, 35), 'Swaps', grey, smallFont)
    )
    
    # Right competitor counters (below visualization)
    window.add_widget(
        widget_id='algo2_comparisons',
        widget=CounterBox((470, 380, 80, 35), 'Comp', grey, smallFont)
    )
    window.add_widget(
        widget_id='algo2_swaps',
        widget=CounterBox((560, 380, 80, 35), 'Swaps', grey, smallFont)
    )
    
    # Algorithm selection dropdowns (below counters)
    window.add_widget(
        widget_id='algo1_dropdown',
        widget=DropdownBox((50, 430, 180, 40), 'Algo 1', grey, smallFont, list(algorithmsDict.keys()), white)
    )
    window.add_widget(
        widget_id='algo2_dropdown',
        widget=DropdownBox((470, 430, 180, 40), 'Algo 2', grey, smallFont, list(algorithmsDict.keys()), white)
    )
    
    # Delay slider (bottom center)
    window.add_widget(
        widget_id='delay_slider',
        widget=SlideBox((280, 430, 150, 40), 'Delay', grey, smallFont)
    )
    
    return window

def init_mode_selection():
    """Initialize the mode selection screen."""
    window = Window(screen)
    
    window.add_widget(
        widget_id='title',
        widget=LabelBox((200, 50, 500, 60), 'Sorting Algorithm Visualizer', dark_blue, titleFont)
    )
    window.add_widget(
        widget_id='subtitle',
        widget=LabelBox((250, 120, 400, 40), 'Select Game Mode', grey, baseFont)
    )
    window.add_widget(
        widget_id='solo_button',
        widget=ModeButtonBox((200, 200, 200, 80), 'Solo Mode', solo_color, baseFont, (80, 130, 200))
    )
    window.add_widget(
        widget_id='arena_button',
        widget=ModeButtonBox((500, 200, 200, 80), 'Arena Mode', arena_color, baseFont, (200, 80, 80))
    )
    window.add_widget(
        widget_id='leaderboard_button',
        widget=ModeButtonBox((350, 330, 200, 60), '🏆 Leaderboard', (60, 160, 80), baseFont, (30, 110, 50))
    )

    return window

def _heat_color(heat_value, heat_threshold):
    """
    Return an RGB color on a green → orange → red gradient.

    heat_value    : accumulated heat for this bar (float)
    heat_threshold: value at which the bar is fully red
    """
    t = min(heat_value / max(heat_threshold, 1), 1.0)   # 0.0 … 1.0
    if t < 0.5:
        # green (0,200,80)  →  orange (255,140,0)
        s = t * 2
        r = int(0   + s * 255)
        g = int(200 + s * (140 - 200))
        b = int(80  + s * (0   - 80))
    else:
        # orange (255,140,0)  →  red (220,30,30)
        s = (t - 0.5) * 2
        r = int(255 + s * (220 - 255))
        g = int(140 + s * (30  - 140))
        b = int(0   + s * 30)
    return (r, g, b)


def drawBars(screen, array, redBar1, redBar2, blueBar1, blueBar2,
             greenRows={}, x_offset=0, width=900, max_height=400, y_offset=0,
             swap_heat=None, heat_threshold=100):
    """Draw the bars and control their colors.

    swap_heat      : optional list[float] of per-bar heat values (same length as array).
                     When provided, bars not currently highlighted use a green→orange→red
                     gradient instead of flat grey.
    heat_threshold : heat value that maps to fully red (default 100).
    """
    numBars = len(array)
    if numBars == 0:
        return
    
    bar_width = width / numBars
    ceil_width = math.ceil(bar_width)
    
    for num in range(numBars):
        if num in (redBar1, redBar2):
            color = red
        elif num in (blueBar1, blueBar2):
            color = blue
        elif num in greenRows:
            color = green
        elif swap_heat is not None:
            color = _heat_color(swap_heat[num], heat_threshold)
        else:
            color = grey
        
        x_pos = x_offset + num * bar_width
        bar_height = array[num]
        y_pos = y_offset + max_height - bar_height
        
        pygame.draw.rect(screen, color, (x_pos, y_pos, ceil_width, bar_height))

def draw_dashed_line(screen, color, start_pos, end_pos, dash_length=5):
    """Draw a dashed line on the screen."""
    x1, y1 = start_pos
    x2, y2 = end_pos
    
    if x1 == x2:  # Vertical line
        for y in range(y1, y2, dash_length * 2):
            pygame.draw.line(screen, color, (x1, y), (x1, min(y + dash_length, y2)))
    else:  # Horizontal line
        for x in range(x1, x2, dash_length * 2):
            pygame.draw.line(screen, color, (x, y1), (min(x + dash_length, x2), y1))

def _make_snapshot(numbers, redBar1, redBar2, blueBar1, blueBar2,
                   swap_heat, comparisons, swaps, elapsed_ms):
    """Return a lightweight snapshot of the current visualizer state.

    All mutable objects are deep-copied so the snapshot is independent of
    any later mutations made to the live arrays.
    """
    return {
        'numbers':    numbers[:],
        'redBar1':    redBar1,
        'redBar2':    redBar2,
        'blueBar1':   blueBar1,
        'blueBar2':   blueBar2,
        'swap_heat':  swap_heat[:],
        'comparisons': comparisons,
        'swaps':      swaps,
        'elapsed_ms': elapsed_ms,
    }


def _restore_snapshot(snap, numbers, swap_heat):
    """Copy snapshot data back into the live state lists in-place.

    Returns (redBar1, redBar2, blueBar1, blueBar2, comparisons, swaps, elapsed_ms).
    """
    numbers[:] = snap['numbers']
    swap_heat[:] = snap['swap_heat']
    return (snap['redBar1'], snap['redBar2'],
            snap['blueBar1'], snap['blueBar2'],
            snap['comparisons'], snap['swaps'],
            snap['elapsed_ms'])


def run_solo_mode():
    """Run the solo mode game loop.

    Playback model
    --------------
    - Play/Stop  : existing ButtonBox – starts a fresh sort / cancels it.
    - Pause/Resume : ToggleButtonBox (⏸) – freezes auto-advance while keeping
                     the iterator alive so step controls still work.
    - Step back  ◀ : restore the previous snapshot from history[].
                     Also bound to the LEFT arrow key.
    - Step fwd   ▶ : advance one step (from future[] if available, else from
                     the live iterator).
                     Also bound to the RIGHT arrow key.

    History system
    --------------
    `history`  – list of snapshots already seen, newest at the end.
    `future`   – list of snapshots that were stepped back over; newest at end.
                 Stepping forward re-applies them without touching the iterator.
                 Any auto-advance or step-fwd past the future tail consumes the
                 live iterator and clears future[] (we are now at the head).
    """
    global game_mode, solo_window

    if solo_window is None:
        solo_window = init_solo_mode()

    window = solo_window

    # ── Live sort state ──────────────────────────────────────────────────────
    numbers: list = []
    isSorting       = False
    sortingIterator = None
    last_iteration  = 0.0
    sort_finished   = False   # True once StopIteration has been raised

    # Elapsed-time tracking
    sort_start_time = 0.0
    elapsed_ms      = 0.0
    current_algorithm = ''
    current_numBars   = 0

    # Swap-heat coloring
    swap_heat:     list = []
    heat_threshold: float = 100.0
    prev_swap_count: int  = 0

    # Highlighted bar indices for the current frame
    redBar1 = redBar2 = blueBar1 = blueBar2 = -1

    # ── Snapshot history ─────────────────────────────────────────────────────
    history: list = []   # snapshots already applied, oldest → newest
    future:  list = []   # snapshots stepped back over, oldest → newest

    # ── Internal helpers ─────────────────────────────────────────────────────
    def _save_to_history():
        """Append the current frame to history (capped at HISTORY_LIMIT)."""
        snap = _make_snapshot(numbers, redBar1, redBar2, blueBar1, blueBar2,
                              swap_heat, get_comparisons(), get_swaps(), elapsed_ms)
        history.append(snap)
        if len(history) > HISTORY_LIMIT:
            history.pop(0)

    def _advance_one_step():
        """Pull one frame from the live iterator (or return False if done)."""
        nonlocal numbers, redBar1, redBar2, blueBar1, blueBar2
        nonlocal elapsed_ms, prev_swap_count, sort_finished
        try:
            numbers, redBar1, redBar2, blueBar1, blueBar2 = next(sortingIterator)
            # Update elapsed time (wall-clock minus pause time is not tracked
            # separately; we accumulate only while actually advancing)
            elapsed_ms = (time.time() - sort_start_time) * 1000
            # Accumulate swap heat for the two active bars
            cur_swaps = get_swaps()
            new_swaps = cur_swaps - prev_swap_count
            if new_swaps > 0:
                for bar_idx in (redBar1, redBar2):
                    if 0 <= bar_idx < len(swap_heat):
                        swap_heat[bar_idx] += new_swaps
            prev_swap_count = cur_swaps
            return True
        except StopIteration:
            sort_finished = True
            return False

    def _update_counters():
        """Push current counter values to the UI widgets."""
        window.set_widget_value('comparisons_counter', get_comparisons())
        window.set_widget_value('swaps_counter',       get_swaps())
        window.set_widget_value('elapsed_counter',     f'{elapsed_ms / 1000:.3f}')

    def _update_step_button_states(is_active):
        """Enable/disable the step buttons depending on whether a sort is active."""
        window.widgets['step_back_btn'].disabled = not is_active
        window.widgets['step_fwd_btn'].disabled  = not is_active
        window.widgets['pause_btn'].disabled     = not is_active

    def _do_step_back():
        """Restore the previous snapshot. Returns True if successful."""
        nonlocal redBar1, redBar2, blueBar1, blueBar2, elapsed_ms, prev_swap_count
        if not history:
            return False
        # Save current state to future before going back
        future.append(_make_snapshot(numbers, redBar1, redBar2, blueBar1, blueBar2,
                                     swap_heat, get_comparisons(), get_swaps(), elapsed_ms))
        snap = history.pop()
        redBar1, redBar2, blueBar1, blueBar2, comps, swps, elapsed_ms = \
            _restore_snapshot(snap, numbers, swap_heat)
        # Restore the global counters to the snapshot values
        reset_counters()
        # Manually set counters to snapshot values via repeated increment would
        # be slow; instead we patch the private globals directly through the
        # counters module's public API by resetting and then bulk-adding.
        import counters as _c
        _c._comparisons = comps
        _c._swaps = swps
        prev_swap_count = swps
        _update_counters()
        return True

    def _do_step_fwd():
        """Advance one step, replaying from future[] if available."""
        nonlocal redBar1, redBar2, blueBar1, blueBar2, elapsed_ms, prev_swap_count
        if sort_finished and not future:
            return False
        # Save current state to history before advancing
        _save_to_history()
        if future:
            # Replay a cached future snapshot (no iterator call needed)
            snap = future.pop()
            redBar1, redBar2, blueBar1, blueBar2, comps, swps, elapsed_ms = \
                _restore_snapshot(snap, numbers, swap_heat)
            import counters as _c
            _c._comparisons = comps
            _c._swaps = swps
            prev_swap_count = swps
            _update_counters()
            return True
        else:
            # At the head — consume the live iterator
            ok = _advance_one_step()
            _update_counters()
            return ok

    # ── Disable step controls until a sort starts ────────────────────────────
    _update_step_button_states(False)

    running_solo = True
    while running_solo:
        screen.fill(white)

        # ── Collect keyboard events before widget update ─────────────────────
        step_back_key = False
        step_fwd_key  = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Keyboard shortcuts for step controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    step_back_key = True
                elif event.key == pygame.K_RIGHT:
                    step_fwd_key = True

            window.update(event)

            # Back button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(820, 10, 70, 30).collidepoint(pygame.mouse.get_pos()):
                    game_mode = MODE_SELECTION
                    return True

        # ── Read widget states ───────────────────────────────────────────────
        delay     = window.get_widget_value('delay_slider') / 10
        isPlaying = window.get_widget_value('play_button')
        isPaused  = window.get_widget_value('pause_btn')

        # Update pause label text to reflect state
        window.set_widget_value('pause_label', 'Run' if isPaused else 'Pause')

        # ── Start a new sort when Play is pressed ────────────────────────────
        if isPlaying and not isSorting:
            reset_counters()
            window.set_widget_value('comparisons_counter', 0)
            window.set_widget_value('swaps_counter',       0)
            window.set_widget_value('elapsed_counter',     '0.000')
            elapsed_ms    = 0.0
            sort_finished = False

            # Clamp array size
            try:
                current_numBars = int(window.get_widget_value('size_input'))
                current_numBars = max(5, min(200, current_numBars))
            except ValueError:
                current_numBars = 100

            numbers = [randint(10, 400) for _ in range(current_numBars)]

            current_algorithm = window.get_widget_value('algorithm_input')
            sortingIterator   = algorithmsDict[current_algorithm](
                numbers, 0, current_numBars - 1)

            isSorting       = True
            sort_start_time = time.time()
            redBar1 = redBar2 = blueBar1 = blueBar2 = -1

            # Reset swap-heat (1.5× size → fully red threshold)
            swap_heat       = [0.0] * current_numBars
            heat_threshold  = max(current_numBars * 1.5, 1)
            prev_swap_count = 0

            # Clear history / future for the new run
            history.clear()
            future.clear()

            # Reset pause toggle if it was left on
            window.set_widget_value('pause_btn', False)

            _update_step_button_states(True)

        # ── Stop clears the sort ─────────────────────────────────────────────
        if not isPlaying:
            isSorting = False
            _update_step_button_states(False)

        # ── Step-back (button OR left-arrow key) ─────────────────────────────
        if isSorting and (window.get_widget_value('step_back_btn') or step_back_key):
            _do_step_back()
            # Stepping while not paused auto-pauses so the user can see the frame
            if not isPaused:
                window.set_widget_value('pause_btn', True)
                isPaused = True

        # ── Step-forward (button OR right-arrow key) ─────────────────────────
        if isSorting and (window.get_widget_value('step_fwd_btn') or step_fwd_key):
            advanced = _do_step_fwd()
            if not isPaused:
                window.set_widget_value('pause_btn', True)
                isPaused = True
            if not advanced and not future:
                # Reached the end via manual stepping — save to DB
                elapsed_ms = (time.time() - sort_start_time) * 1000
                window.set_widget_value('elapsed_counter', f'{elapsed_ms / 1000:.3f}')
                save_record(
                    algorithm=current_algorithm,
                    array_size=current_numBars,
                    swaps=get_swaps(),
                    comparisons=get_comparisons(),
                    elapsed_ms=elapsed_ms,
                )
                isSorting = False
                window.set_widget_value('play_button', False)
                window.set_widget_value('pause_btn',   False)
                _update_step_button_states(False)

        # ── Auto-advance when playing and not paused ─────────────────────────
        if isSorting and not isPaused:
            try:
                if time.time() - last_iteration >= delay:
                    # Save snapshot before advancing so we can step back to it
                    _save_to_history()
                    # Any auto-advance invalidates the cached future
                    future.clear()
                    advanced = _advance_one_step()
                    last_iteration = time.time()
                    _update_counters()

                    if not advanced:
                        # Sort completed naturally
                        elapsed_ms = (time.time() - sort_start_time) * 1000
                        window.set_widget_value('elapsed_counter', f'{elapsed_ms / 1000:.3f}')
                        save_record(
                            algorithm=current_algorithm,
                            array_size=current_numBars,
                            swaps=get_swaps(),
                            comparisons=get_comparisons(),
                            elapsed_ms=elapsed_ms,
                        )
                        isSorting = False
                        window.set_widget_value('play_button', False)
                        window.set_widget_value('pause_btn',   False)
                        _update_step_button_states(False)
            except Exception:
                pass   # guard against any unexpected iterator error

        # ── Draw ─────────────────────────────────────────────────────────────
        if isSorting:
            drawBars(screen, numbers, redBar1, redBar2, blueBar1, blueBar2,
                     x_offset=VIZ_X_OFFSET, width=VIZ_WIDTH,
                     max_height=VIZ_MAX_H,  y_offset=VIZ_Y_OFFSET,
                     swap_heat=swap_heat, heat_threshold=heat_threshold)
        else:
            drawBars(screen, numbers, -1, -1, -1, -1,
                     x_offset=VIZ_X_OFFSET, width=VIZ_WIDTH,
                     max_height=VIZ_MAX_H,  y_offset=VIZ_Y_OFFSET,
                     greenRows=set(range(len(numbers))))

        window.render()
        pygame.display.update()

def run_arena_mode():
    """Run the arena mode game loop."""
    global game_mode, arena_window
    
    if arena_window is None:
        arena_window = init_arena_mode()
    
    window = arena_window
    array1 = []
    array2 = []
    original_array = []
    isPlaying = False
    isSorting = False
    iterator1 = None
    iterator2 = None
    last_iteration = 0
    algo1_finished = False
    algo2_finished = False
    winner = None
    
    running_arena = True
    while running_arena:
        screen.fill(white)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            window.update(event)
            
            # Check back button
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                back_rect = pygame.Rect(820, 10, 70, 30)
                if back_rect.collidepoint(mouse_pos):
                    game_mode = MODE_SELECTION
                    return True
        
        # Get delay in seconds
        delay = window.get_widget_value('delay_slider') / 10
        
        isPlaying = window.get_widget_value('play_button')
        if isPlaying and not isSorting:
            # Reset everything for new battle
            reset_counters('algo1')
            reset_counters('algo2')
            window.set_widget_value('algo1_comparisons', 0)
            window.set_widget_value('algo1_swaps', 0)
            window.set_widget_value('algo2_comparisons', 0)
            window.set_widget_value('algo2_swaps', 0)
            window.set_widget_value('winner_label', '')
            
            # Generate shared random array
            try:
                numBars = int(window.get_widget_value('size_input'))
                if numBars < 5:
                    numBars = 5
                elif numBars > 100:
                    numBars = 100
            except ValueError:
                numBars = 50
            original_array = [randint(10, 300) for i in range(numBars)]
            array1 = original_array.copy()
            array2 = original_array.copy()
            
            # Initialize both sorting iterators
            algo1_name = window.get_widget_value('algo1_dropdown')
            algo2_name = window.get_widget_value('algo2_dropdown')
            
            iterator1 = algorithmsDict[algo1_name](array1, 0, numBars - 1)
            iterator2 = algorithmsDict[algo2_name](array2, 0, numBars - 1)
            
            isSorting = True
            algo1_finished = False
            algo2_finished = False
            winner = None
        
        if not isPlaying:
            isSorting = False
        
        if isSorting:
            should_update = time.time() - last_iteration >= delay
            
            if should_update:
                last_iteration = time.time()
                
                # Step algorithm 1
                if not algo1_finished:
                    try:
                        set_current_instance('algo1')
                        array1, red1, red2, blue1, blue2 = next(iterator1)
                        window.set_widget_value('algo1_comparisons', get_comparisons('algo1'))
                        window.set_widget_value('algo1_swaps', get_swaps('algo1'))
                    except StopIteration:
                        algo1_finished = True
                        if winner is None:
                            winner = window.get_widget_value('algo1_dropdown') + ' WINS!'
                            window.set_widget_value('winner_label', winner)
                
                # Step algorithm 2
                if not algo2_finished:
                    try:
                        set_current_instance('algo2')
                        array2, red1, red2, blue1, blue2 = next(iterator2)
                        window.set_widget_value('algo2_comparisons', get_comparisons('algo2'))
                        window.set_widget_value('algo2_swaps', get_swaps('algo2'))
                    except StopIteration:
                        algo2_finished = True
                        if winner is None:
                            winner = window.get_widget_value('algo2_dropdown') + ' WINS!'
                            window.set_widget_value('winner_label', winner)
                
                # Reset current instance
                set_current_instance(None)
                
                # Both finished
                if algo1_finished and algo2_finished:
                    isSorting = False
                    window.set_widget_value('play_button', False)
            
            # Draw both visualizations
            # Left side - Algorithm 1
            drawBars(screen, array1, -1, -1, -1, -1, greenRows=set(range(len(array1))) if algo1_finished else {},
                     x_offset=50, width=400, max_height=320, y_offset=50)
            
            # Right side - Algorithm 2
            drawBars(screen, array2, -1, -1, -1, -1, greenRows=set(range(len(array2))) if algo2_finished else {},
                     x_offset=470, width=400, max_height=320, y_offset=50)
            
            # Draw divider
            draw_dashed_line(screen, grey, (450, 50), (450, 370))
            
            # Draw algorithm names above visualizations
            label1 = smallFont.render(window.get_widget_value('algo1_dropdown'), True, dark_blue)
            screen.blit(label1, (50, 35))
            label2 = smallFont.render(window.get_widget_value('algo2_dropdown'), True, dark_blue)
            screen.blit(label2, (470, 35))
            
            window.render()
            pygame.display.update()
            
        else:
            # Draw static arrays when not sorting
            drawBars(screen, array1, -1, -1, -1, -1, greenRows=set(range(len(array1))),
                     x_offset=50, width=400, max_height=320, y_offset=50)
            drawBars(screen, array2, -1, -1, -1, -1, greenRows=set(range(len(array2))),
                     x_offset=470, width=400, max_height=320, y_offset=50)
            
            draw_dashed_line(screen, grey, (450, 50), (450, 370))
            
            if array1:
                label1 = smallFont.render(window.get_widget_value('algo1_dropdown'), True, dark_blue)
                screen.blit(label1, (50, 35))
            if array2:
                label2 = smallFont.render(window.get_widget_value('algo2_dropdown'), True, dark_blue)
                screen.blit(label2, (470, 35))
            
            window.render()
            pygame.display.update()

# ---------------------------------------------------------------------------
# Leaderboard helpers
# ---------------------------------------------------------------------------

# Maps the display label shown in the sort-by dropdown to the DB column name
_SORT_FIELD_MAP = {
    'Time (s)':     'elapsed_ms',
    'Swaps':        'swaps',
    'Comparisons':  'comparisons',
    'Array Size':   'array_size',
    'Algorithm':    'algorithm',
    'Date':         'created_at',
}

_SORT_FIELDS = list(_SORT_FIELD_MAP.keys())


def _build_leaderboard_window():
    """Create and return the leaderboard Window with all its widgets."""
    window = Window(screen)

    # Title
    window.add_widget(
        'lb_title',
        LabelBox((0, 0, 900, 40), 'Leaderboard  –  Solo Mode', dark_blue, baseFont)
    )

    # --- Filter row (y=45) ---
    # "Algorithm:" label
    window.add_widget(
        'filter_label',
        LabelBox((10, 45, 90, 30), 'Algorithm:', grey, smallFont)
    )
    # Algorithm filter dropdown  (populated dynamically each time we open leaderboard)
    window.add_widget(
        'filter_algo',
        DropdownBox((100, 45, 160, 30), '', grey, smallFont, ['All'], white, direction='down')
    )

    # "Sort by:" label
    window.add_widget(
        'sort_label',
        LabelBox((280, 45, 60, 30), 'Sort by:', grey, smallFont)
    )
    # Sort-field dropdown
    window.add_widget(
        'sort_field',
        DropdownBox((340, 45, 120, 30), '', grey, smallFont, _SORT_FIELDS, white, direction='down')
    )

    # ASC / DESC toggle
    window.add_widget(
        'sort_asc',
        ToggleButtonBox((470, 45, 60, 30), 'ASC', smallFont,
                        color_off=(130, 130, 130), color_on=(50, 150, 80))
    )

    # Refresh button
    window.add_widget(
        'refresh_btn',
        LabelBox((545, 45, 80, 30), '⟳ Refresh', white, smallFont, (80, 130, 200))
    )

    # Export CSV button
    window.add_widget(
        'export_btn',
        LabelBox((635, 45, 90, 30), '⬇ Export CSV', white, smallFont, (60, 160, 80))
    )

    # Export status message (shown briefly after export)
    window.add_widget(
        'export_status',
        LabelBox((550, 10, 260, 28), '', grey, smallFont)
    )

    # Back button
    window.add_widget(
        'back_button',
        LabelBox((820, 10, 70, 30), 'Back', white, smallFont, grey)
    )

    # Record count label
    window.add_widget(
        'record_count',
        LabelBox((730, 45, 160, 30), '', grey, smallFont)
    )

    # --- Table (y=85, fills the rest of the screen) ---
    table_rect = (0, 85, 900, 415)
    window.add_widget(
        'lb_table',
        LeaderboardTable(table_rect, tinyFont, smallFont)
    )

    return window


def _refresh_leaderboard(window):
    """Read DB and push fresh records into the table widget."""
    # Rebuild algorithm filter list from DB
    algos_in_db = get_algorithms()
    filter_options = ['All'] + algos_in_db

    # Patch the dropdown options list in-place (simpler than recreating widget)
    filter_widget = window.widgets['filter_algo']
    filter_widget.options = filter_options
    # Keep selection valid
    if filter_widget.selected_option >= len(filter_options):
        filter_widget.selected_option = 0

    selected_algo = filter_widget.options[filter_widget.selected_option]

    sort_widget = window.widgets['sort_field']
    sort_label = sort_widget.options[sort_widget.selected_option]
    sort_col = _SORT_FIELD_MAP.get(sort_label, 'elapsed_ms')

    sort_asc = window.get_widget_value('sort_asc')  # True = ASC toggle active

    records = get_records(
        filter_algorithm=selected_algo,
        sort_by=sort_col,
        sort_asc=sort_asc,
    )
    window.widgets['lb_table'].set_records(records)
    window.set_widget_value(
        'record_count',
        f'{len(records)} record{"s" if len(records) != 1 else ""}'
    )


def _do_export(lb_window):
    """Export current view to CSV and update the status label."""
    filter_widget = lb_window.widgets['filter_algo']
    selected_algo = filter_widget.options[filter_widget.selected_option]

    sort_widget = lb_window.widgets['sort_field']
    sort_label  = sort_widget.options[sort_widget.selected_option]
    sort_col    = _SORT_FIELD_MAP.get(sort_label, 'elapsed_ms')
    sort_asc    = lb_window.get_widget_value('sort_asc')

    # Save next to the DB file, in the src/ directory
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'leaderboard_{timestamp}.csv'
    out_dir  = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, filename)

    try:
        n = export_csv(out_path,
                       filter_algorithm=selected_algo,
                       sort_by=sort_col,
                       sort_asc=sort_asc)
        lb_window.set_widget_value('export_status', f'Saved {n} rows to {filename} ✓')
    except Exception as exc:
        lb_window.set_widget_value('export_status', f'Error: {exc}')

    return time.time()   # caller stores this to clear the label later


def run_leaderboard():
    """Run the leaderboard screen."""
    global game_mode

    lb_window = _build_leaderboard_window()
    _refresh_leaderboard(lb_window)

    # Track previous filter/sort state to auto-refresh on change
    prev_algo_idx   = lb_window.widgets['filter_algo'].selected_option
    prev_sort_idx   = lb_window.widgets['sort_field'].selected_option
    prev_asc        = lb_window.get_widget_value('sort_asc')

    export_msg_time = 0.0   # timestamp when status message was set

    running_lb = True
    while running_lb:
        screen.fill(white)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            lb_window.update(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Back button
                if pygame.Rect(820, 10, 70, 30).collidepoint(mouse_pos):
                    game_mode = MODE_SELECTION
                    return True

                # Explicit refresh button
                if pygame.Rect(545, 45, 80, 30).collidepoint(mouse_pos):
                    _refresh_leaderboard(lb_window)
                    prev_algo_idx = lb_window.widgets['filter_algo'].selected_option
                    prev_sort_idx = lb_window.widgets['sort_field'].selected_option
                    prev_asc      = lb_window.get_widget_value('sort_asc')

                # Export CSV button
                if pygame.Rect(635, 45, 90, 30).collidepoint(mouse_pos):
                    export_msg_time = _do_export(lb_window)

        # Clear export status message after 3 seconds
        if export_msg_time and time.time() - export_msg_time > 3.0:
            lb_window.set_widget_value('export_status', '')
            export_msg_time = 0.0

        # Auto-refresh when filter/sort controls change
        cur_algo_idx = lb_window.widgets['filter_algo'].selected_option
        cur_sort_idx = lb_window.widgets['sort_field'].selected_option
        cur_asc      = lb_window.get_widget_value('sort_asc')

        if (cur_algo_idx != prev_algo_idx or
                cur_sort_idx != prev_sort_idx or
                cur_asc != prev_asc):
            _refresh_leaderboard(lb_window)
            prev_algo_idx = cur_algo_idx
            prev_sort_idx = cur_sort_idx
            prev_asc      = cur_asc

        lb_window.render()
        pygame.display.update()


def run_mode_selection():
    """Run the mode selection screen."""
    global game_mode
    
    window = init_mode_selection()
    
    running_selection = True
    while running_selection:
        screen.fill(white)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            window.update(event)
            
            # Check if a mode was selected
            if window.get_widget_value('solo_button'):
                game_mode = SOLO_MODE
                return True
            elif window.get_widget_value('arena_button'):
                game_mode = ARENA_MODE
                return True
            elif window.get_widget_value('leaderboard_button'):
                game_mode = LEADERBOARD_MODE
                return True
        
        window.render()
        pygame.display.update()

def main():
    """Main game loop with mode switching."""
    global game_mode, solo_window, arena_window
    
    running = True
    while running:
        if game_mode == MODE_SELECTION:
            running = run_mode_selection()
        elif game_mode == SOLO_MODE:
            running = run_solo_mode()
        elif game_mode == ARENA_MODE:
            running = run_arena_mode()
        elif game_mode == LEADERBOARD_MODE:
            running = run_leaderboard()
    
    pygame.quit()


if __name__ == '__main__':
    main()

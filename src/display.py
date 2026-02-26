import pygame
from math import ceil
from time import time
from abc import ABC, abstractmethod

class Window:
    def __init__(self, screen):
        self.screen = screen
        self.widgets = {}

    def add_widget(self, widget_id, widget):
        self.widgets[widget_id] = widget

    def get_widget_value(self, widget_id):
        return self.widgets[widget_id].get_value()

    def set_widget_value(self, widget_id, value):
        return self.widgets[widget_id].set_value(value)

    def render(self):
        """Two-pass render: base widgets first, then open dropdown overlays on top."""
        for widget in self.widgets.values():
            widget.render(self.screen)

        # Second pass: re-render any open DropdownBox so its panel floats above
        # every other widget (including tables that were added later).
        for widget in self.widgets.values():
            if isinstance(widget, DropdownBox) and widget.openDropdown:
                widget.render_overlay(self.screen)

    def update(self, event):
        for widget in self.widgets.values():
            widget.update(event)
        

class Box:
    def __init__(self, rect):
        self.isActive = False
        self.rect     = pygame.Rect(rect)
    
    def update(self, event):
        self.mousePos = pygame.mouse.get_pos()
        self.clicked  = event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(self.mousePos)
        self.hovered = self.rect.collidepoint(self.mousePos)


class InputBox(ABC, Box):
    def __init__(self, rect, label, color, font):
        super().__init__(rect)
        self.label  = label
        self.color = color
        self.font = font
        
    def render(self, screen):
        label = self.font.render(self.label, True, self.color)
        screen.blit(label, (self.rect.x + (self.rect.w - label.get_width()) / 2, self.rect.y - 32))
        pygame.draw.rect(screen, self.color, self.rect, 2)

    @abstractmethod
    def get_value(self):
        pass

    @abstractmethod
    def set_value(self, value):
        pass


class TextBox(InputBox):
    def __init__(self, rect, label, color, font, text):
        super().__init__(rect, label, color, font)
        self.text = text
    
    def render(self, screen):
        super().render(screen)
        surface = self.font.render(self.text, True, self.color)
        screen.blit(surface, surface.get_rect(center=self.rect.center))

    def update(self, event):
        super().update(event)
        if self.hovered and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE: 
                self.text = self.text[:-1]
            elif event.unicode.isdigit(): 
                self.text += event.unicode
        
    def get_value(self):
        return self.text

    def set_value(self, value):
        self.text = value


class SlideBox(InputBox):
    def __init__(self, rect, label, color, font):
        super().__init__(rect, label, color, font)
        self.start = self.rect.x + 6
        self.end   = self.rect.x + self.rect.w - 6
        self.value = self.start
        self.dragging = False  # Track if the user is dragging the slider

    def render(self, screen):
        super().render(screen)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        pygame.draw.line(screen, self.color, (self.start, self.rect.y + 25), (self.end, self.rect.y + 25), 2)
        pygame.draw.line(screen, self.color, (self.value, self.rect.y + 5), (self.value, self.rect.y + 45), 12)

    def update(self, event):
        super().update(event)
        self.start  = self.rect.x + 6
        self.end    = self.rect.x + self.rect.w - 6
        
        # Check if the mouse is clicking on the slider knob
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(self.mousePos):
            if self.start <= self.mousePos[0] <= self.end:
                self.dragging = True

        # Stop dragging when the mouse button is released
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        # If dragging, move the slider with the mouse
        if self.dragging:
            self.value = min(max(self.mousePos[0], self.start), self.end)  # Restrict the slider's movement within bounds
        

    def get_value(self):
        # Normalize the value to a range between 0 and 1
        normalized_value = (self.value - self.start) / (self.end - self.start)
        return normalized_value

    def set_value(self, value):
        # Set the value within the range [start, end] based on a normalized input
        self.value = self.start + value * (self.end - self.start)

class ButtonBox(Box):
    def __init__(self, rect, inactive_img_path, active_img_path):
        super().__init__(rect)
        self.inactive_img = pygame.image.load(inactive_img_path)
        self.inactive_img = pygame.transform.scale(self.inactive_img, (rect[2], rect[3]))
        self.active_img = pygame.image.load(active_img_path)
        self.active_img = pygame.transform.scale(self.active_img, (rect[2], rect[3]))
        self.active = False
    
    def render(self, screen):
        img = self.active_img if self.active else self.inactive_img
        screen.blit(img, (self.rect.x, self.rect.y))

    def update(self, event):
        super().update(event)
        if self.clicked:
            self.active = not self.active

    def get_value(self):
        return self.active

    def set_value(self, value):
        self.active = value


class CounterBox(Box):
    """A display box for showing counter values like comparisons and swaps."""
    
    def __init__(self, rect, label, color, font):
        super().__init__(rect)
        self.label = label
        self.color = color
        self.font = font
        self.value = 0
    
    def render(self, screen):
        # Draw label above the counter
        label_surface = self.font.render(self.label, True, self.color)
        screen.blit(label_surface, (self.rect.x, self.rect.y - 25))
        
        # Draw the counter value box
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        # Render the value
        value_text = self.font.render(str(self.value), True, self.color)
        text_rect = value_text.get_rect(center=self.rect.center)
        screen.blit(value_text, text_rect)
    
    def update(self, event):
        super().update(event)
        # Counter box is display-only, no interaction needed
    
    def get_value(self):
        return self.value
    
    def set_value(self, value):
        self.value = value


class ModeButtonBox(Box):
    """A button for selecting game mode (Solo or Arena)."""
    
    def __init__(self, rect, label, color, font, selected_color):
        super().__init__(rect)
        self.label = label
        self.color = color
        self.font = font
        self.selected_color = selected_color
        self.selected = False
    
    def render(self, screen):
        # Draw button with different color if selected
        color = self.selected_color if self.selected else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (50, 50, 50), self.rect, 2, border_radius=10)
        
        # Render label
        label_surface = self.font.render(self.label, True, (250, 250, 250))
        text_rect = label_surface.get_rect(center=self.rect.center)
        screen.blit(label_surface, text_rect)
    
    def update(self, event):
        super().update(event)
        if self.clicked:
            self.selected = True
    
    def get_value(self):
        return self.selected
    
    def set_value(self, value):
        self.selected = value


class LabelBox(Box):
    """A simple label display box."""
    
    def __init__(self, rect, text, color, font, bg_color=None):
        super().__init__(rect)
        self.text = text
        self.color = color
        self.font = font
        self.bg_color = bg_color
    
    def render(self, screen):
        if self.bg_color:
            pygame.draw.rect(screen, self.bg_color, self.rect)
        label_surface = self.font.render(self.text, True, self.color)
        text_rect = label_surface.get_rect(center=self.rect.center)
        screen.blit(label_surface, text_rect)
    
    def update(self, event):
        super().update(event)
    
    def get_value(self):
        return self.text
    
    def set_value(self, value):
        self.text = value


class StepButtonBox(Box):
    """
    A one-shot click button drawn as a filled rounded rectangle with a
    centred unicode symbol (e.g. '◀' or '▶').

    Unlike ToggleButtonBox it does NOT stay pressed — get_value() returns
    True only for the single frame in which the button was clicked, then
    resets to False automatically.  This makes it easy to poll in a game
    loop without extra bookkeeping.
    """

    def __init__(self, rect, symbol, font,
                 color=(80, 80, 80),
                 hover_color=(120, 120, 120),
                 disabled_color=(50, 50, 50),
                 text_color=(240, 240, 240),
                 disabled_text_color=(100, 100, 100)):
        super().__init__(rect)
        self.symbol = symbol
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.disabled_color = disabled_color
        self.text_color = text_color
        self.disabled_text_color = disabled_text_color
        self._fired = False   # True for exactly one frame after a click
        self.disabled = False # When True the button ignores clicks and dims

    def render(self, screen):
        if self.disabled:
            bg = self.disabled_color
            fg = self.disabled_text_color
        elif self.hovered:
            bg = self.hover_color
            fg = self.text_color
        else:
            bg = self.color
            fg = self.text_color

        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, (30, 30, 30), self.rect, 2, border_radius=6)
        surf = self.font.render(self.symbol, True, fg)
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def update(self, event):
        super().update(event)
        # Reset the fired flag every frame so callers see at most one True
        self._fired = False
        if not self.disabled and self.clicked:
            self._fired = True

    def get_value(self):
        """Returns True for exactly the frame in which the button was clicked."""
        return self._fired

    def set_value(self, value):
        """Programmatically fire (True) or clear (False) the button."""
        self._fired = bool(value)


class ToggleButtonBox(Box):
    """A simple rectangular toggle button (on/off)."""

    def __init__(self, rect, label, font,
                 color_off=(100, 100, 100), color_on=(50, 150, 255),
                 text_color=(250, 250, 250)):
        super().__init__(rect)
        self.label = label
        self.font = font
        self.color_off = color_off
        self.color_on = color_on
        self.text_color = text_color
        self.active = False

    def render(self, screen):
        color = self.color_on if self.active else self.color_off
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, (30, 30, 30), self.rect, 2, border_radius=6)
        surf = self.font.render(self.label, True, self.text_color)
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def update(self, event):
        super().update(event)
        if self.clicked:
            self.active = not self.active

    def get_value(self):
        return self.active

    def set_value(self, value):
        self.active = bool(value)


class LeaderboardTable(Box):
    """
    A scrollable table widget that renders leaderboard rows.

    Columns displayed (fixed order):
        Rank | Algorithm | Size | Swaps | Comparisons | Time (ms) | Date
    """

    COLUMNS = [
        ('Rank',        40),
        ('Algorithm',  160),
        ('Size',        50),
        ('Swaps',       80),
        ('Comparisons', 100),
        ('Time (s)',     90),
        ('Date',        150),
    ]
    ROW_HEIGHT = 28
    HEADER_HEIGHT = 32

    def __init__(self, rect, font, header_font,
                 bg_color=(240, 240, 255),
                 row_color=(255, 255, 255),
                 alt_row_color=(220, 225, 245),
                 header_color=(30, 30, 120),
                 border_color=(100, 100, 100),
                 text_color=(20, 20, 20),
                 header_text_color=(250, 250, 250)):
        super().__init__(rect)
        self.font = font
        self.header_font = header_font
        self.bg_color = bg_color
        self.row_color = row_color
        self.alt_row_color = alt_row_color
        self.header_color = header_color
        self.border_color = border_color
        self.text_color = text_color
        self.header_text_color = header_text_color

        self.records = []          # list of dicts from database.get_records()
        self.scroll_offset = 0    # first visible row index
        self._visible_rows = 0    # computed each render

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def set_records(self, records: list):
        self.records = records
        self.scroll_offset = 0

    def get_value(self):
        return self.records

    def set_value(self, value):
        """Set the table records. Expects a list of dictionaries."""
        self.set_records(value)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------
    def update(self, event):
        super().update(event)
        if not self.rect.collidepoint(pygame.mouse.get_pos()):
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:   # scroll up
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.button == 5:  # scroll down
                max_offset = max(0, len(self.records) - self._visible_rows)
                self.scroll_offset = min(self.scroll_offset + 1, max_offset)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def render(self, screen):
        # Background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)

        # Clip drawing to the table rect
        clip_rect = screen.get_clip()
        screen.set_clip(self.rect)

        x_start = self.rect.x
        y_header = self.rect.y

        # --- Header row ---
        pygame.draw.rect(screen, self.header_color,
                         (x_start, y_header, self.rect.width, self.HEADER_HEIGHT))
        x = x_start
        for col_name, col_w in self.COLUMNS:
            surf = self.header_font.render(col_name, True, self.header_text_color)
            screen.blit(surf, (x + 4, y_header + (self.HEADER_HEIGHT - surf.get_height()) // 2))
            x += col_w
            # vertical divider
            pygame.draw.line(screen, self.border_color,
                             (x - 1, y_header), (x - 1, y_header + self.HEADER_HEIGHT))

        # --- Data rows ---
        body_y = y_header + self.HEADER_HEIGHT
        available_h = self.rect.height - self.HEADER_HEIGHT
        self._visible_rows = available_h // self.ROW_HEIGHT

        for i in range(self._visible_rows):
            row_idx = self.scroll_offset + i
            if row_idx >= len(self.records):
                break
            rec = self.records[row_idx]
            row_y = body_y + i * self.ROW_HEIGHT
            row_color = self.row_color if i % 2 == 0 else self.alt_row_color
            pygame.draw.rect(screen, row_color,
                             (x_start, row_y, self.rect.width, self.ROW_HEIGHT))

            values = [
                str(row_idx + 1),
                rec.get('algorithm', ''),
                str(rec.get('array_size', '')),
                str(rec.get('swaps', '')),
                str(rec.get('comparisons', '')),
                f"{rec.get('elapsed_ms', 0) / 1000:.3f}",
                rec.get('created_at', '')[:16],   # trim seconds
            ]
            x = x_start
            for val, (_, col_w) in zip(values, self.COLUMNS):
                surf = self.font.render(val, True, self.text_color)
                screen.blit(surf, (x + 4, row_y + (self.ROW_HEIGHT - surf.get_height()) // 2))
                x += col_w
                pygame.draw.line(screen, self.border_color,
                                 (x - 1, row_y), (x - 1, row_y + self.ROW_HEIGHT))

            # horizontal row divider
            pygame.draw.line(screen, self.border_color,
                             (x_start, row_y + self.ROW_HEIGHT - 1),
                             (x_start + self.rect.width, row_y + self.ROW_HEIGHT - 1))

        # --- Scrollbar ---
        total = len(self.records)
        if total > self._visible_rows and self._visible_rows > 0:
            sb_x = self.rect.right - 8
            sb_h = available_h
            thumb_h = max(20, int(sb_h * self._visible_rows / total))
            max_offset = total - self._visible_rows
            thumb_y = body_y + int((sb_h - thumb_h) * self.scroll_offset / max_offset) if max_offset else body_y
            pygame.draw.rect(screen, (180, 180, 200), (sb_x, body_y, 8, sb_h))
            pygame.draw.rect(screen, self.header_color, (sb_x, thumb_y, 8, thumb_h))

        screen.set_clip(clip_rect)


class DropdownBox(InputBox):

    VISIBLE_OPTIONS = 8

    def __init__(self, rect, label, color, font, options, options_background_color,
                 direction='up'):
        """
        direction : 'up'   – list expands above the box (default, original behaviour)
                    'down' – list expands below the box (use when box is near the top)
        """
        super().__init__(rect, label, color, font)
        self.openDropdown = False
        self.options = options
        self.options_background_color = options_background_color
        self.direction = direction

        self._update_dropdown_rect()
        self.scroll_offset = 0  # Current scroll position
        self.scrollbar_width = 5  # Width of the scrollbar
        self.selected_option = 0  # Index of the selected option

    def _update_dropdown_rect(self):
        """Recompute the dropdown panel rect based on current direction."""
        if self.direction == 'down':
            self.dropdown_rect = pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height,          # starts just below the box
                self.rect.width,
                self.rect.height * self.VISIBLE_OPTIONS,
            )
        else:  # 'up'
            self.dropdown_rect = pygame.Rect(
                self.rect.x,
                self.rect.y - self.rect.height * self.VISIBLE_OPTIONS,
                self.rect.width,
                self.rect.height * self.VISIBLE_OPTIONS,
            )

    def render(self, screen):
        """Draw the base box + selected value.  The open panel is drawn
        separately by render_overlay() so it always appears above other widgets."""
        super().render(screen)

        # Render the selected option in the input box
        option_text = self.font.render(self.options[self.selected_option], 1, self.color)
        screen.blit(option_text, option_text.get_rect(center=self.rect.center))

        # For dropdowns that open upward the panel is NOT overlaid by anything,
        # so we draw it inline here as before.  For downward dropdowns the
        # Window's second render pass calls render_overlay() instead.
        if self.openDropdown and self.direction != 'down':
            self._draw_panel(screen)

    def render_overlay(self, screen):
        """Draw the floating panel on top of all other widgets.
        Called by Window.render() as a second pass for open dropdowns."""
        if self.openDropdown:
            self._draw_panel(screen)

    def _draw_panel(self, screen):
        """Draw the dropdown option list and scrollbar."""
        # Dropdown background
        pygame.draw.rect(screen, self.options_background_color, self.dropdown_rect)
        pygame.draw.rect(screen, self.color, self.dropdown_rect, 2)

        # Visible options
        start_index = self.scroll_offset
        end_index = min(start_index + self.VISIBLE_OPTIONS, len(self.options))

        for index in range(start_index, end_index):
            rect = self.rect.copy()
            if self.direction == 'down':
                rect.y = self.rect.y + self.rect.height + (index - start_index) * self.rect.height
            else:
                rect.y = self.rect.y - (index - start_index + 1) * self.rect.height

            pygame.draw.rect(screen, self.options_background_color, rect)
            pygame.draw.rect(screen, self.color, rect, 1)
            option_text = self.font.render(self.options[index], 1, self.color)
            screen.blit(option_text, option_text.get_rect(center=rect.center))

        self.render_scrollbar(screen)

    def render_scrollbar(self, screen):
        total_options = len(self.options)
        if total_options > self.VISIBLE_OPTIONS:
            proportion_visible = self.VISIBLE_OPTIONS / total_options
            scrollbar_height = int(self.dropdown_rect.height * proportion_visible)

            max_scroll = total_options - self.VISIBLE_OPTIONS
            proportion_scrolled = self.scroll_offset / max_scroll if max_scroll > 0 else 0
            scrollbar_rect = pygame.Rect(self.dropdown_rect.right - self.scrollbar_width,
                                         self.dropdown_rect.y + proportion_scrolled * (self.dropdown_rect.height - scrollbar_height),
                                         self.scrollbar_width, scrollbar_height)

            # Draw the scrollbar (visual only)
            pygame.draw.rect(screen, self.color, scrollbar_rect)

    def update(self, event):
        super().update(event)

        # Toggle the dropdown when the input box is clicked
        if self.clicked:
            self.openDropdown = not self.openDropdown

        if self.openDropdown:
            # Handle mouse wheel scrolling
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    self.scroll_offset = max(self.scroll_offset - 1, 0)
                elif event.button == 5:  # Scroll down
                    self.scroll_offset = min(self.scroll_offset + 1, len(self.options) - self.VISIBLE_OPTIONS)

            # Handle option selection
            self.handle_option_selection(event)

    def handle_option_selection(self, event):
        start_index = self.scroll_offset
        for index in range(start_index, start_index + self.VISIBLE_OPTIONS):
            rect = self.rect.copy()
            if self.direction == 'down':
                rect.y = self.rect.y + self.rect.height + (index - start_index) * self.rect.height
            else:
                rect.y = self.rect.y - (index - start_index + 1) * self.rect.height

            if rect.collidepoint(pygame.mouse.get_pos()) and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.selected_option = index
                self.openDropdown = False  # Close dropdown after selecting

    def get_value(self):
        return self.options[self.selected_option]

    def set_value(self, value):
        self.selected_option = value

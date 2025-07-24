from contextlib import redirect_stdout
with redirect_stdout(None):
    import pygame


class KeyButton:
    # Position will taken as bottom-left
    def __init__(
        self, window, position: tuple[int, int], dimensions: tuple[int, int], border_width: int,
        trail_width: int, trail_length: int, trail_speed: float, trail_offset: float,
        background_color, pressed_background_color, border_color, label_color, counter_color, trail_color,
        font, label: str, label_font_size: int, counter_font_size: int, label_rotation: int,
        show_label: bool, show_counter: bool,
    ):
        self.window = window
        self.position = position
        self.dimensions = dimensions
        self.rect = pygame.Rect(position[0], position[1], dimensions[0], dimensions[1])
        self.rect.bottomleft = position
        self.border_width = border_width
        self.trail_bottom = self.rect.top + trail_offset

        self.background_color = background_color
        self.pressed_background_color = pressed_background_color
        self.border_color = border_color
        self.label_color = label_color
        self.counter_color = counter_color
        self.trail_color = trail_color

        # Label only needs to be rendered once
        self.key = label
        self.show_label = show_label
        self.label = pygame.font.Font(font, label_font_size).render(label, True, self.label_color)
        self.label = pygame.transform.rotate(self.label, label_rotation)
        self.label.set_alpha(self.label_color[3])
        # Meanwhile, counter will be rerendered every frame
        self.counter_font = pygame.font.Font(font, counter_font_size)
        self.show_counter = show_counter

        self.trail_width = trail_width
        self.trail_length = trail_length
        self.trail_speed = trail_speed
        self.trails: list[Trail] = []

        self.last_frame_pressed = False
        self.last_frame_time = None

    def draw(self, current_keys: set[str], memory_keys: dict[str, int]):
        if self.window is None:
            return
        
        currently_pressed = self.key in current_keys
        if self.key == '\\':
            currently_pressed = '\\\\' in current_keys
        
        if self.trail_length > 0:
            # Move, add, and render trails
            ## Move all trails up
            keeping_trails = []
            for trail in self.trails:
                trail.move(self.trail_speed)
                if trail.is_visible():
                    # Keep trails that are still visible
                    keeping_trails.append(trail)
            
            ## Add new trail if newly pressed
            if currently_pressed and not self.last_frame_pressed:
                keeping_trails.append(Trail(self.trail_length))
            ## Extend bottom trail if held since last frame
            elif currently_pressed and self.last_frame_pressed and len(keeping_trails):
                keeping_trails[-1].set_bottom(0)
            self.trails = keeping_trails

            ## Render trails
            for trail in self.trails:
                trail_rect = pygame.Rect(self.rect.left, self.trail_bottom - trail.top, self.trail_width, trail.length())
                trail_rect.centerx = self.rect.centerx

                trail_box = pygame.Surface(trail_rect.size)
                trail_box.set_alpha(self.trail_color[3])
                trail_box.fill(self.trail_color)
                self.window.blit(trail_box, trail_rect)

        # Render button
        border_box = pygame.Surface((self.rect.size[0] + self.border_width, self.rect.size[1] + self.border_width))
        border_box.set_alpha(self.border_color[3])
        pygame.draw.rect(border_box, self.border_color, ((0, 0), self.rect.size), self.border_width)
        self.window.blit(border_box, self.rect)

        back_box = pygame.Surface((self.rect.size[0] - 2 * self.border_width, self.rect.size[1] - 2 * self.border_width))
        back_box.set_alpha(self.pressed_background_color[3] if currently_pressed else self.background_color[3])
        back_box.fill(self.pressed_background_color if currently_pressed else self.background_color)
        self.window.blit(back_box, (self.rect.left + self.border_width, self.rect.top + self.border_width))

        if self.show_label:
            self.window.blit(self.label, self.label.get_rect(center=self.rect.center))

        if self.show_counter:
            counter_surface = self.counter_font.render(str(memory_keys.get(self.key, 0)), True, self.counter_color)
            counter_surface.set_alpha(self.counter_color[3])
            self.window.blit(counter_surface, counter_surface.get_rect(centerx=self.rect.centerx, bottom=self.rect.bottom))

        self.last_frame_pressed = currently_pressed


class Trail:
    def __init__(self, maximum, bottom=0, top=0):
        self.maximum = maximum
        self.bottom = bottom
        self.top = top

    def move(self, amount: float):
        self.bottom += amount
        self.top = min(self.top + amount, self.maximum)
    
    def length(self) -> float:
        return self.top - self.bottom
    
    def set_bottom(self, bottom: float):
        self.bottom = bottom
    
    def is_visible(self) -> bool:
        return self.bottom <= self.maximum

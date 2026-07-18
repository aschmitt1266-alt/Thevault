from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

FONT_FILE = ASSETS / "vault_font.ttf"
FONT_NAME = "VaultFont"

if FONT_FILE.exists():
    LabelBase.register(name=FONT_NAME, fn_regular=str(FONT_FILE))
else:
    FONT_NAME = "Roboto"

YELLOW = (1.00, 0.88, 0.10, 1)
GREEN = (0.16, 0.42, 0.18, 1)
BRIGHT_GREEN = (0.24, 0.62, 0.24, 1)
DARK = (0.02, 0.03, 0.035, 0.95)
WHITE = (0.96, 0.98, 0.94, 1)


@dataclass(frozen=True)
class SystemInfo:
    key: str
    title: str
    games: tuple[str, ...]


SYSTEMS = (
    SystemInfo("nes", "NES", ("Super Mario Bros. 3", "The Legend of Zelda", "Mega Man 2", "Metroid")),
    SystemInfo("snes", "SNES", ("Super Mario World", "Donkey Kong Country", "Chrono Trigger", "Mega Man X")),
    SystemInfo("genesis", "GENESIS", ("Sonic 2", "Streets of Rage 2", "Gunstar Heroes", "Shinobi III")),
    SystemInfo("n64", "NINTENDO 64", ("Super Mario 64", "Mario Kart 64", "GoldenEye 007", "Star Fox 64")),
    SystemInfo("ps1", "PLAYSTATION", ("Crash Bandicoot", "Tekken 3", "Metal Gear Solid", "Tony Hawk's Pro Skater 2")),
    SystemInfo("ps2", "PLAYSTATION 2", ("PS2 support will be added later.",)),
)


class VaultButton(Button):
    selected = BooleanProperty(False)
    normal_fill = ListProperty([0.02, 0.035, 0.035, 0.95])
    selected_fill = ListProperty([0.18, 0.48, 0.20, 1.0])

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("color", WHITE)
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("font_size", sp(22))
        kwargs.setdefault("bold", True)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)

        with self.canvas.before:
            self._fill_color = Color(*self.normal_fill)
            self._fill = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])

        with self.canvas.after:
            self._outline_color = Color(*YELLOW)
            self._outline = Line(
                rounded_rectangle=(*self.pos, *self.size, dp(18)),
                width=dp(1.5),
            )

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            selected=self._redraw,
            state=self._redraw,
        )
        self.bind(size=self._sync_text)

    def _sync_text(self, *_):
        self.text_size = (
            max(0, self.width - dp(18)),
            max(0, self.height - dp(10)),
        )

    def _redraw(self, *_):
        active = self.selected or self.state == "down"

        self._fill.pos = self.pos
        self._fill.size = self.size
        self._outline.rounded_rectangle = (*self.pos, *self.size, dp(18))

        if active:
            self._fill_color.rgba = self.selected_fill
            self._outline_color.rgba = YELLOW
            self._outline.width = dp(5)
            self.color = (1, 1, 1, 1)
        else:
            self._fill_color.rgba = self.normal_fill
            self._outline_color.rgba = (0.90, 0.78, 0.08, 1)
            self._outline.width = dp(1.5)
            self.color = WHITE


class BackgroundScreen(Screen):
    def __init__(self, background_filename: str, **kwargs):
        super().__init__(**kwargs)

        self.layout = FloatLayout()

        self.background = Image(
            source=str(ASSETS / background_filename),
            fit_mode="cover",
            allow_stretch=True,
            keep_ratio=False,
        )
        self.layout.add_widget(self.background)

        self.content = FloatLayout()
        self.layout.add_widget(self.content)
        self.add_widget(self.layout)


class SplashScreen(BackgroundScreen):
    def __init__(self, **kwargs):
        super().__init__("splash.png", **kwargs)

        panel = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint=(0.72, None),
            height=dp(72),
            pos_hint={"center_x": 0.5, "y": 0.045},
        )

        self.status = Label(
            text="OPENING THE VAULT...",
            font_name=FONT_NAME,
            font_size=sp(17),
            bold=True,
            color=WHITE,
        )

        self.progress = ProgressBar(max=100, value=0)

        panel.add_widget(self.status)
        panel.add_widget(self.progress)
        self.content.add_widget(panel)

    def on_enter(self):
        self.progress.value = 0
        Clock.schedule_interval(self._advance, 0.035)

    def _advance(self, _dt):
        self.progress.value += 2.5
        if self.progress.value >= 100:
            Clock.unschedule(self._advance)
            self.manager.current = "systems"
            return False
        return True


class SelectableScreen(BackgroundScreen):
    def __init__(self, background_filename: str, columns: int, **kwargs):
        super().__init__(background_filename, **kwargs)
        self.columns = columns
        self.buttons: list[VaultButton] = []
        self.selected_index = 0

    def select(self, index: int):
        if not self.buttons:
            return

        self.selected_index = max(0, min(index, len(self.buttons) - 1))

        for number, button in enumerate(self.buttons):
            button.selected = number == self.selected_index

        selected = self.buttons[self.selected_index]
        if hasattr(selected, "scroll_to"):
            selected.scroll_to(selected)

    def move_left(self):
        if self.selected_index % self.columns > 0:
            self.select(self.selected_index - 1)

    def move_right(self):
        if (
            self.selected_index % self.columns < self.columns - 1
            and self.selected_index + 1 < len(self.buttons)
        ):
            self.select(self.selected_index + 1)

    def move_up(self):
        target = self.selected_index - self.columns
        if target >= 0:
            self.select(target)

    def move_down(self):
        target = self.selected_index + self.columns
        if target < len(self.buttons):
            self.select(target)

    def activate_selected(self):
        if self.buttons:
            self.buttons[self.selected_index].trigger_action(duration=0.08)


class SystemsScreen(SelectableScreen):
    def __init__(self, on_system: Callable[[SystemInfo], None], **kwargs):
        super().__init__("systems.png", columns=2, **kwargs)

        grid = GridLayout(
            cols=2,
            rows=3,
            spacing=(dp(18), dp(14)),
            padding=(dp(22), dp(12)),
            size_hint=(0.84, 0.63),
            pos_hint={"center_x": 0.5, "y": 0.055},
        )

        for system in SYSTEMS:
            button = VaultButton(text=system.title)
            button.bind(on_release=lambda _button, item=system: on_system(item))
            grid.add_widget(button)
            self.buttons.append(button)

        self.content.add_widget(grid)
        self.select(0)


class GamesScreen(SelectableScreen):
    def __init__(self, on_back: Callable[[], None], **kwargs):
        super().__init__("games.png", columns=2, **kwargs)
        self.current_system: SystemInfo | None = None
        self.on_back_callback = on_back

        self.system_label = Label(
            text="",
            font_name=FONT_NAME,
            font_size=sp(24),
            bold=True,
            color=YELLOW,
            size_hint=(0.70, 0.08),
            pos_hint={"center_x": 0.5, "top": 0.79},
        )
        self.content.add_widget(self.system_label)

        self.scroll = ScrollView(
            size_hint=(0.82, 0.48),
            pos_hint={"center_x": 0.5, "y": 0.17},
            do_scroll_x=False,
        )

        self.game_grid = GridLayout(
            cols=2,
            spacing=(dp(16), dp(12)),
            padding=(dp(4), dp(4)),
            size_hint_y=None,
            row_default_height=dp(68),
            row_force_default=True,
        )
        self.game_grid.bind(minimum_height=self.game_grid.setter("height"))

        self.scroll.add_widget(self.game_grid)
        self.content.add_widget(self.scroll)

        self.back_button = VaultButton(
            text="BACK",
            size_hint=(0.25, 0.095),
            pos_hint={"x": 0.09, "y": 0.045},
        )
        self.back_button.bind(on_release=lambda *_: self.on_back_callback())
        self.content.add_widget(self.back_button)

        self.message = Label(
            text="",
            font_name=FONT_NAME,
            font_size=sp(14),
            color=WHITE,
            size_hint=(0.53, 0.09),
            pos_hint={"right": 0.91, "y": 0.045},
            halign="right",
            valign="middle",
        )
        self.message.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.content.add_widget(self.message)

    def load_system(self, system: SystemInfo):
        self.current_system = system
        self.system_label.text = system.title
        self.message.text = "CONTROLLER TEST BUILD"

        self.game_grid.clear_widgets()
        self.buttons = []

        for title in system.games:
            button = VaultButton(text=title)
            button.bind(
                on_release=lambda _button, game=title: self.choose_game(game)
            )
            self.game_grid.add_widget(button)
            self.buttons.append(button)

        self.select(0)
        self.scroll.scroll_y = 1

    def choose_game(self, game_title: str):
        self.message.text = f"{game_title} SELECTED"


class VaultApp(App):
    title = "The Vault"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.axis_state = {0: 0, 1: 0}
        self.last_controller_action = 0.0

    def build(self):
        Window.clearcolor = (0.01, 0.015, 0.02, 1)

        Window.bind(
            on_key_down=self._on_key_down,
            on_joy_hat=self._on_joy_hat,
            on_joy_axis=self._on_joy_axis,
            on_joy_button_down=self._on_joy_button_down,
        )

        self.manager = ScreenManager(
            transition=FadeTransition(duration=0.16)
        )

        self.splash = SplashScreen(name="splash")
        self.systems = SystemsScreen(self.open_system, name="systems")
        self.games = GamesScreen(self.go_back, name="games")

        self.manager.add_widget(self.splash)
        self.manager.add_widget(self.systems)
        self.manager.add_widget(self.games)

        return self.manager

    def open_system(self, system: SystemInfo):
        self.games.load_system(system)
        self.manager.current = "games"

    def go_back(self):
        self.manager.current = "systems"

    def _active_selectable(self):
        current = self.manager.current_screen
        return current if isinstance(current, SelectableScreen) else None

    def _controller_move(self, direction: str):
        screen = self._active_selectable()
        if screen is None:
            return

        if direction == "left":
            screen.move_left()
        elif direction == "right":
            screen.move_right()
        elif direction == "up":
            screen.move_up()
        elif direction == "down":
            screen.move_down()

    def _controller_activate(self):
        screen = self._active_selectable()
        if screen is not None:
            screen.activate_selected()

    def _controller_back(self):
        if self.manager.current == "games":
            self.go_back()

    def _on_key_down(self, _window, key, _scancode, _codepoint, _modifiers):
        key_map = {
            273: "up",
            274: "down",
            276: "left",
            275: "right",
            19: "up",
            20: "down",
            21: "left",
            22: "right",
        }

        if key in key_map:
            self._controller_move(key_map[key])
            return True

        if key in (13, 23, 32, 96):
            self._controller_activate()
            return True

        if key in (27, 4, 97):
            self._controller_back()
            return True

        return False

    def _on_joy_hat(self, _window, _stickid, _hatid, value):
        # Kivy normally reports D-pad as a tuple:
        # left=(-1,0), right=(1,0), up=(0,1), down=(0,-1)
        try:
            x, y = value
        except (TypeError, ValueError):
            return False

        if x < 0:
            self._controller_move("left")
        elif x > 0:
            self._controller_move("right")
        elif y > 0:
            self._controller_move("up")
        elif y < 0:
            self._controller_move("down")

        return True

    def _on_joy_axis(self, _window, _stickid, axisid, value):
        # Xbox left stick commonly appears as axis 0 and 1.
        if axisid not in (0, 1):
            return False

        deadzone = 16000

        if value > deadzone:
            direction = 1
        elif value < -deadzone:
            direction = -1
        else:
            direction = 0

        old_direction = self.axis_state.get(axisid, 0)
        self.axis_state[axisid] = direction

        # Fire only when crossing out of the center deadzone.
        if direction == 0 or direction == old_direction:
            return False

        if axisid == 0:
            self._controller_move("right" if direction > 0 else "left")
        else:
            self._controller_move("down" if direction > 0 else "up")

        return True

    def _on_joy_button_down(self, _window, _stickid, buttonid):
        # Common Xbox/Kivy mappings vary by Android device.
        # These groups intentionally cover the common A/B assignments.
        a_buttons = {0, 96}
        b_buttons = {1, 97}

        if buttonid in a_buttons:
            self._controller_activate()
            return True

        if buttonid in b_buttons:
            self._controller_back()
            return True

        return False

    def on_pause(self):
        return True


if __name__ == "__main__":
    VaultApp().run()

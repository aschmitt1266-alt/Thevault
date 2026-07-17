from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

YELLOW = (0.95, 0.84, 0.14, 1)
GREEN = (0.18, 0.38, 0.20, 1)
DARK = (0.035, 0.045, 0.06, 0.94)
WHITE = (0.92, 0.95, 0.90, 1)
MUTED = (0.62, 0.69, 0.61, 1)


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
    SystemInfo("ps2", "PLAYSTATION 2", ("This system is reserved for the next test build.",)),
)


class VaultButton(ButtonBehavior, Label):
    selected = NumericProperty(0)
    normal_color = ListProperty([0.055, 0.075, 0.065, 0.92])
    selected_color = ListProperty([0.18, 0.38, 0.20, 0.98])

    def __init__(self, **kwargs):
        kwargs.setdefault("font_size", sp(25))
        kwargs.setdefault("bold", True)
        kwargs.setdefault("color", WHITE)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)
        self.bind(size=self._sync_text, pos=self._redraw, selected=self._redraw)
        with self.canvas.before:
            self._bg_color = Color(*self.normal_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
        with self.canvas.after:
            self._line_color = Color(*YELLOW)
            self._line = Line(rounded_rectangle=(*self.pos, *self.size, dp(18)), width=1.4)

    def _sync_text(self, *_):
        self.text_size = (self.width - dp(20), self.height - dp(12))
        self._redraw()

    def _redraw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._line.rounded_rectangle = (*self.pos, *self.size, dp(18))
        self._bg_color.rgba = self.selected_color if self.selected else self.normal_color
        self._line.width = 3 if self.selected else 1.4


class BackgroundScreen(Screen):
    background_source = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = FloatLayout()
        self.bg = Image(source=self.background_source, fit_mode="cover")
        self.root_layout.add_widget(self.bg)
        self.overlay = FloatLayout()
        self.root_layout.add_widget(self.overlay)
        self.add_widget(self.root_layout)


class SplashScreen(BackgroundScreen):
    def __init__(self, **kwargs):
        kwargs["background_source"] = str(ASSETS / "splash.png")
        super().__init__(**kwargs)

        panel = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint=(0.76, None),
            height=dp(95),
            pos_hint={"center_x": 0.5, "y": 0.075},
        )
        self.status = Label(
            text="Opening The Vault...",
            color=WHITE,
            font_size=sp(20),
            bold=True,
            size_hint_y=0.45,
        )
        self.progress = ProgressBar(max=100, value=0, size_hint_y=0.30)
        panel.add_widget(self.status)
        panel.add_widget(self.progress)
        self.overlay.add_widget(panel)

    def on_enter(self):
        self.progress.value = 0
        Clock.schedule_interval(self._advance, 0.035)

    def _advance(self, dt):
        self.progress.value += 2.2
        if self.progress.value >= 100:
            Clock.unschedule(self._advance)
            self.manager.current = "systems"
            return False
        return True


class SelectableScreen(BackgroundScreen):
    buttons: list[VaultButton]
    selected_index = NumericProperty(0)

    def select(self, index: int):
        if not self.buttons:
            return
        self.selected_index = index % len(self.buttons)
        for i, button in enumerate(self.buttons):
            button.selected = int(i == self.selected_index)

    def move(self, delta: int):
        self.select(self.selected_index + delta)

    def activate_selected(self):
        if self.buttons:
            self.buttons[self.selected_index].trigger_action(duration=0.06)


class SystemsScreen(SelectableScreen):
    def __init__(self, on_system: Callable[[SystemInfo], None], **kwargs):
        kwargs["background_source"] = str(ASSETS / "systems.png")
        super().__init__(**kwargs)
        self.buttons = []

        holder = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 0.72),
            pos_hint={"x": 0, "y": 0.02},
        )
        grid = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint=(0.78, None),
        )
        grid.bind(minimum_height=grid.setter("height"))

        for system in SYSTEMS:
            btn = VaultButton(text=system.title, size_hint_y=None, height=dp(64))
            btn.bind(on_release=lambda _btn, s=system: on_system(s))
            grid.add_widget(btn)
            self.buttons.append(btn)

        holder.add_widget(grid)
        self.overlay.add_widget(holder)
        self.select(0)


class GamesScreen(SelectableScreen):
    current_system = None

    def __init__(self, on_back: Callable[[], None], **kwargs):
        kwargs["background_source"] = str(ASSETS / "games.png")
        super().__init__(**kwargs)
        self.buttons = []
        self.on_back_callback = on_back

        self.system_title = Label(
            text="",
            color=YELLOW,
            font_size=sp(28),
            bold=True,
            size_hint=(0.9, 0.08),
            pos_hint={"center_x": 0.5, "top": 0.80},
        )
        self.overlay.add_widget(self.system_title)

        self.scroll = ScrollView(
            size_hint=(0.86, 0.54),
            pos_hint={"center_x": 0.5, "y": 0.13},
            do_scroll_x=False,
        )
        self.list_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None,
            padding=(0, dp(4)),
        )
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        self.overlay.add_widget(self.scroll)

        back = VaultButton(
            text="BACK",
            size_hint=(0.28, None),
            height=dp(54),
            pos_hint={"x": 0.07, "y": 0.035},
        )
        back.bind(on_release=lambda *_: self.on_back_callback())
        self.overlay.add_widget(back)
        self.back_button = back

        self.message = Label(
            text="",
            color=WHITE,
            font_size=sp(17),
            size_hint=(0.58, 0.08),
            pos_hint={"right": 0.93, "y": 0.025},
            halign="right",
            valign="middle",
        )
        self.message.bind(size=lambda inst, value: setattr(inst, "text_size", value))
        self.overlay.add_widget(self.message)

    def load_system(self, system: SystemInfo):
        self.current_system = system
        self.system_title.text = system.title
        self.message.text = "First build: interface test only"
        self.list_layout.clear_widgets()
        self.buttons = []

        for game in system.games:
            btn = VaultButton(text=game, size_hint_y=None, height=dp(64))
            btn.bind(on_release=lambda _btn, title=game: self.launch_placeholder(title))
            self.list_layout.add_widget(btn)
            self.buttons.append(btn)

        self.select(0)
        self.scroll.scroll_y = 1

    def launch_placeholder(self, game_title: str):
        self.message.text = f'"{game_title}" selected — emulator hookup comes next.'


class VaultApp(App):
    title = "The Vault"

    def build(self):
        Window.clearcolor = (0.02, 0.025, 0.035, 1)
        Window.bind(on_key_down=self._on_key_down)

        self.manager = ScreenManager(transition=FadeTransition(duration=0.18))
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

    def _on_key_down(self, _window, key, _scancode, _codepoint, _modifiers):
        screen = self._active_selectable()
        if screen is None:
            return False

        # Android/desktop keyboard and common controller key mappings.
        if key in (273, 19):       # up
            screen.move(-1)
            return True
        if key in (274, 20):       # down
            screen.move(1)
            return True
        if key in (13, 32, 23, 96):  # enter/space/dpad-center/controller A
            screen.activate_selected()
            return True
        if key in (27, 4, 97):     # escape/android back/controller B
            if self.manager.current == "games":
                self.go_back()
                return True
        return False

    def on_pause(self):
        return True


if __name__ == "__main__":
    VaultApp().run()

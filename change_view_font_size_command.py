"""
This is a modified version of Default/font.py to change
font size of the current view instead of entire application.
"""

import sublime
import sublime_plugin

from typing import Union


def clear_view_font_size(view: Union[sublime.View, None]):
    if view is None:
        return

    view_settings = view.settings()
    view_settings.erase('font_size')

class IncreaseFontSizeCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Preferences.sublime-settings')
        clear_view_font_size(self.window.active_view())
        current = settings.get('font_size', 10)

        if current >= 36:
            current += 4
        elif current >= 24:
            current += 2
        else:
            current += 0.5

        if current > 128:
            current = 128
        self.window.status_message(f'Font size: {current}')
        settings.set('font_size', current)

class DecreaseFontSizeCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Preferences.sublime-settings')
        clear_view_font_size(self.window.active_view())
        current = settings.get('font_size', 10)

        if current >= 40:
            current -= 4
        elif current >= 26:
            current -= 2
        else:
            current -= 0.5

        if current < 8:
            current = 8

        self.window.status_message(f'Font size: {current}')        
        settings.set('font_size', current)

class IncreaseViewFontSizeCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit):
        settings = self.view.settings()
        current = settings.get('font_size', 10)

        if current >= 36:
            current += 4
        elif current >= 24:
            current += 2
        else:
            current += 0.5

        if current > 128:
            current = 128

        window = self.view.window()
        if window is not None:
            window.status_message(f'View font size: {current}')
        settings.set('font_size', current)

class DecreaseViewFontSizeCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit):
        settings = self.view.settings()
        current = settings.get('font_size', 10)

        if current >= 40:
            current -= 4
        elif current >= 26:
            current -= 2
        else:
            current -= 0.5

        if current < 8:
            current = 8

        window = self.view.window()
        if window is not None:
            window.status_message(f'View font size: {current}')        
        settings.set('font_size', current)

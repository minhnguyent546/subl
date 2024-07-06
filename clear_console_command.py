"""Clear sublime text console content."""

import sublime
import sublime_plugin


class ClearConsoleCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        settings = sublime.load_settings('Preferences.sublime-settings')
        previous = settings.get('console_max_history_lines')
        settings.set('console_max_history_lines', 1)
        print("")
        settings.set('console_max_history_lines', previous)

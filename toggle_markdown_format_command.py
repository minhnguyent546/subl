"""
Toggle format between normal Markdown and DMOJ-style Markdown.

DMOJ uses `~` for inline math instead of `$`. For example:
- Normal Markdown: $y = x^2$
- DMOJ Markdown: ~y = x^2~
"""

import sublime
import sublime_plugin

import subprocess
from pathlib import Path


class ConvertToDmojCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit):
        file_name = self.view.file_name()
        if file_name is None:
            # unsaved file
            return

        file_extension = Path(file_name).suffix
        file_extension = file_extension.lower()
        if file_extension != '.md':
            # not a markdown file
            return

        command = [
            r'sed',
            r'-r',
            # r'-e', r'/./,$!d', # remove leading blank lines
            r'-e', r's/\$([^$]+)\$/~\1~/g',
            r'-e', r's/\$~/$$/g',
            r'-e', r's/~\$/$$/g'
        ]
        with open(file_name, 'r', encoding='utf-8') as file:
            completed_process = subprocess.run(command, input=file.read().encode(), capture_output=True)

            result_content = completed_process.stdout.decode()
            self.view.replace(edit, sublime.Region(0, self.view.size()), result_content)


class RestoreFromDmojCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit):
        file_name = self.view.file_name()
        if file_name is None:
            # unsaved file
            return

        file_extension = Path(file_name).suffix
        file_extension = file_extension.lower()
        if file_extension != '.md':
            # not a markdown file
            return

        command = [
            r'sed',
            r'-r',
            # r'-e', r'/./,$!d', # remove leading blank lines
            r'-e', r's/~([^~]+)~/$\1$/g',
        ]
        with open(file_name, 'r', encoding='utf-8') as file:
            completed_process = subprocess.run(command, input=file.read().encode(), capture_output=True)

            result_content = completed_process.stdout.decode()
            self.view.replace(edit, sublime.Region(0, self.view.size()), result_content)

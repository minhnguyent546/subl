"""Show path of the current file on the status bar."""

import sublime
import sublime_plugin

import os


def show_file_path(view: sublime.View):
    window = view.window()
    if window is None:
        return

    file_name = view.file_name()
    if file_name is None:
        # file is unsaved
        return

    opened_dirs = window.folders()
    for opened_dir in opened_dirs:
        if file_name.startswith(opened_dir):
            opened_dir_basename = os.path.basename(opened_dir)
            clipped_file_name = file_name[len(opened_dir) - len(opened_dir_basename):]
            view.set_status('_file_path', '[' + clipped_file_name + ']')
            break
    else:
        view.erase_status('_file_path')

class ShowFilePathOnStatusBarListener(sublime_plugin.EventListener):
    def on_activated(self, view: sublime.View):
        """Called when a view gains input focus."""
        show_file_path(view)

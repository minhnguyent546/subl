"""Select all comments in a file."""

import sublime
import sublime_plugin


class SelectAllCommentsCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit):
        regions = self.view.find_by_selector('comment')
        for region in regions:
            if region.empty():
                continue

            assert region.a < region.b
            if self.view.substr(region.b - 1) == '\n':
                region.b -= 1

        self.view.sel().clear()
        self.view.sel().add_all(regions)

"""Move file of current view to parent directory."""

import sublime
import sublime_plugin

import os


def _go_up(path: str, level: int = 1) -> str:
    if path.endswith('/'):
        path = path[:-1]

    new_path = path
    for _ in range(level):
        new_path = os.path.dirname(new_path)

    return new_path

class MoveFileUpCommand(sublime_plugin.WindowCommand):
    def run(self, level: int = 1):
        view = self.window.active_view()
        assert view is not None

        file_name = view.file_name()
        assert file_name is not None
        file_basename = os.path.basename(file_name)

        dir_name = os.path.dirname(file_name)
        new_dir_name = _go_up(dir_name, level)
        new_file_name = os.path.join(new_dir_name, file_basename)

        if sublime.ok_cancel_dialog(f'Move file to {new_file_name}?'):
            try:
                if os.path.isfile(new_file_name):
                    raise OSError('file already exists')

                os.rename(file_name, new_file_name)
                view.retarget(new_file_name) 
            except OSError as e:
                sublime.status_message('Unable to move file: ' + str(e))
            except:
                sublime.status_message('Unable to move file')

    def is_enabled(self) -> bool:
        view = self.window.active_view()
        return view is not None and view.file_name() is not None

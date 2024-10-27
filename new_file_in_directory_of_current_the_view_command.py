"""Create new file/Duplicate file in the same directory of the current view."""

import sublime
import sublime_plugin

import os
from typing import List, Tuple, Union


class FileNameInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, view: sublime.View, opened_folders: Union[List[str], None] = None):
        self.new_file_base_name = 'new_file'

        cur_view_file_name = view.file_name() or view.name()
        self.ext = os.path.splitext(cur_view_file_name)[1]

        self.cur_dir = os.path.dirname(cur_view_file_name)
        if opened_folders is not None:
            for folder in opened_folders:
                if self.cur_dir.startswith(folder):
                    dir_base_name = os.path.basename(folder)
                    self.cur_dir = '@/' + self.cur_dir[len(folder) - len(dir_base_name):]
                    break

        logged_user = os.getlogin()
        if self.cur_dir.startswith(f'/home/{logged_user}'):
            self.cur_dir = self.cur_dir.replace(f'/home/{logged_user}', '~')


    def name(self) -> str:
        return 'file_name'

    def placeholder(self) -> str:
        return 'Enter file name'

    def initial_text(self) -> str:
        return self.new_file_base_name + self.ext

    def initial_selection(self) -> List[Tuple[int, int]]:
        return [
            (0, len(self.new_file_base_name)),
        ]

    def preview(self, text: str) -> sublime.Html:
        cur_path = os.path.join(self.cur_dir, text)
        return sublime.Html(f'<strong>{cur_path}</strong>')

    def validate(self, text: str) -> bool:
        return len(text) > 0


class NewFileInDirectoryOfTheCurrentViewCommand(sublime_plugin.WindowCommand):
    def is_enabled(self) -> bool:
        """
        The command will be enabled if there is a view in the window and
        the file in that view is saved to disk
        """

        # a normal comment block
        view = self.window.active_view()  # an inline comment
        if view is None or view.file_name() is None:
            return False

        return True

    def run(self, file_name: str, duplicate_file: bool = False):
        view = self.window.active_view()
        assert view is not None

        cur_view_file_name = view.file_name()
        assert cur_view_file_name is not None


        branch, leaf = os.path.split(cur_view_file_name)
        new_file_path = os.path.join(branch, file_name)

        try:
            if os.path.isfile(new_file_path):
                raise OSError('file already exists')

            new_dirname = os.path.dirname(new_file_path)
            if not os.path.exists(new_dirname):
                os.makedirs(new_dirname)
            open(new_file_path, 'w').close()  # create new file

            # how do I copy the content of the current view to the new file?
            if duplicate_file:
                with open(cur_view_file_name, 'r') as f:
                    content = f.read()
                    with open(new_file_path, 'w') as new_f:
                        new_f.write(content)
                self.window.status_message('Duplicated file: ' + new_file_path)
            else:
                self.window.status_message('Created file: ' + new_file_path)
            self.window.open_file(new_file_path)

        except OSError as e:
            sublime.status_message('Unable to create file: ' + str(e))
        except:
            sublime.status_message('Unable to create file')

    def input(self, args) -> Union[sublime_plugin.TextInputHandler, None]:
        view = self.window.active_view()
        if view is None or view.file_name() is None:
            return None

        if 'file_name' not in args:
            return FileNameInputHandler(view, self.window.folders())

        return None

    def input_description(self) -> str:
        return 'New file'

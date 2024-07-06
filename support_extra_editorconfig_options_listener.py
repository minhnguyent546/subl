"""
Add support for some .editorconfig options which sublime text does not natively support.
Currently, the only added option is `max_line_length`.
"""

import sublime
import sublime_plugin

from editorconfig import get_properties, EditorConfigError


def config_extra_options(view: sublime.View):
    file_name = view.file_name()
    if file_name is None:
        return

    settings = view.settings()
    rulers = settings.get('rulers', [])
    try:
        editorconfig_options = get_properties(file_name)
        if editorconfig_options is None:
            return

        # max_line_length option
        max_line_length = editorconfig_options.get('max_line_length', None)
        if max_line_length is None:
            return

        if max_line_length == 'off':
            settings.set('rulers', [])
        elif max_line_length.isdigit():
            max_line_length = int(max_line_length)
            # all ruler length that larger than `max_line_length` will be dropped
            in_rulers = False
            new_rulers = []
            for ruler in rulers:
                if isinstance(ruler, int):
                    if ruler > max_line_length:
                        continue
                    if ruler == max_line_length:
                        in_rulers = True
                elif isinstance(ruler, list):
                    if (len(ruler) == 0 or ruler[0] > max_line_length):
                        continue
                    if ruler[0] == max_line_length:
                        in_rulers = True

                new_rulers.append(ruler)

            if not in_rulers:
                new_rulers.append(max_line_length)
            settings.set('rulers', new_rulers)

    except EditorConfigError as e:
        print(f'Cannot read editorconfig options: {e}')
    except Exception as e:
        print(f'Cannot read editorconfig options: {e}')

class SupportExtraEditorconfigOptionsEventListener(sublime_plugin.EventListener):
    def on_clone(self, view: sublime.View):
        config_extra_options(view)
        
    def on_load(self, view: sublime.View):
        config_extra_options(view)

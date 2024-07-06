"""
Splitting function call arguments into multiple lines or joining them into a single line.

For instance:
    hello_world(1, 2, x=[1, 2, 3]), after splitting:
    hello_world(
        1,
        2,
        x=[1, 2, 3],
    )
"""

import sublime
import sublime_plugin

from typing import List, Literal


class FormatFunctionCallArgumentsCommand(sublime_plugin.TextCommand):
    def is_enabled(self) -> bool:
        syntax = self.view.settings().get('syntax')
        return syntax == 'Packages/Python/Python.sublime-syntax'

    def run(self, edit: sublime.Edit, option: Literal['split', 'join']):
        view = self.view
        func_call_selectors = [
            'meta.function-call.arguments.python',
        ]
        use_spaces = view.settings().get('translate_tabs_to_spaces', False)
        tab_size = view.settings().get('tab_size', 4)
        tab_chars = " " * tab_size if use_spaces else '\t'
        
        new_regions: List[sublime.Region] = []
        for region in view.sel():
            for selector in func_call_selectors:
                if (
                    view.match_selector(region.begin(), selector) and
                    view.match_selector(region.end(), selector)
                ):
                    break
            else:
                continue

            # get correct scope name
            scope_name = view.scope_name(region.begin())
            right_index = -1
            for selector in func_call_selectors:
                right_index = scope_name.rfind(selector)
                if right_index != -1:
                    break
            assert right_index != -1
            scope_name = scope_name[:right_index + len(selector)]
            arguments_region = view.expand_to_scope(region.begin(), scope_name)
            if arguments_region is None:
                continue

            func_call_arguments = parse_arguments(view, arguments_region)
            if option == 'split':
                indent_level = view.indentation_level(arguments_region.begin())
                arg_indent = tab_chars * (indent_level + 1)
                parenthesis_indent = tab_chars * indent_level

                formated_arguments_str = f',\n{arg_indent}'.join(func_call_arguments)
                formated_arguments_str = arg_indent + formated_arguments_str

                # add '(' and ')'
                formated_arguments_str = '(' + '\n' + formated_arguments_str
                formated_arguments_str += ',\n' + parenthesis_indent + ')'
            elif option == 'join':
                formated_arguments_str = ', '.join(func_call_arguments)
                formated_arguments_str = '(' + formated_arguments_str + ')'
            else:
                continue

            view.replace(edit, arguments_region, formated_arguments_str)
            new_regions.append(sublime.Region(arguments_region.begin() + len(formated_arguments_str) - 1))

        view.sel().clear()
        self.view.sel().add_all(new_regions)

def parse_arguments(view: sublime.View, region: sublime.Region) -> List[str]:
    text = view.substr(region)[1:-1]  # ignore '(' and ')'
    arguments = [arg.strip() for arg in text.split(',')]
    arguments = [arg for arg in arguments if arg]
    return arguments

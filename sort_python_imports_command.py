"""A simple plugin for sorting python import statements."""

import ast
from functools import cmp_to_key
from typing import List, Optional, Tuple

import sublime
import sublime_plugin


class SortPythonImportsCommand(sublime_plugin.TextCommand):
    def is_enabled(self) -> bool:
        settings = self.view.settings()
        python_syntax = 'Packages/Python/Python.sublime-syntax'
        return settings.get('syntax') == python_syntax

    def run(self, edit: sublime.Edit): 
        regions = self.view.find_by_selector('meta.statement.import')
        if not regions:
            return

        # import statements can have inline comment associated with them,
        # so we need to expand the region to cover that comment
        regions = [self.view.line(region) for region in regions]

        assoc_comments: List[Optional[str]] = [None for _ in range(len(regions))]
        for idx, region in enumerate(regions):
            current_line = self.view.substr(self.view.line(region))
            comment_symb_idx = current_line.rfind('#')
            if comment_symb_idx != -1:
                assoc_comments[idx] = current_line[comment_symb_idx:]

        # insert two lines after import statements
        last_import_row = self.view.rowcol(regions[-1].end())[0]
        cur_row = last_import_row + 1
        view_num_rows = self.view.rowcol(self.view.size())[0]

        # find the first non-empty line
        while (cur_row < view_num_rows):
            is_empty_line = self.line_content(cur_row).strip() == ''
            if not is_empty_line:
                break
            cur_row += 1

        # spaces between imports and the rest must be at least 2 (except for __all__ magic variable)
        # add extra lines if necessary
        while cur_row - last_import_row <= 2:
            if (
                self.starts_with_magic_var(self.line_content(cur_row)) and
                cur_row - last_import_row == 2
            ):
                break
            self.view.insert(edit, self.view.text_point(cur_row, 0), '\n')
            cur_row += 1

        # remove redundant lines
        num_lines_to_remove = cur_row - last_import_row - 3
        if self.starts_with_magic_var(self.line_content(cur_row)):
            num_lines_to_remove += 1
        for _ in range(0, num_lines_to_remove):
            cur_row -= 1
            assert self.line_content(cur_row).strip() == ''
            self.view.erase(edit, self.view.full_line(self.view.text_point(cur_row, 0)))

        import_section_regions: List[List[Tuple[sublime.Region, Optional[str]]]] = []
        for idx in range(len(regions)):
            region = regions[idx]
            if idx == 0 or self.view.rowcol(region.begin())[0] > self.view.rowcol(regions[idx - 1].end())[0] + 1:
                import_section_regions.append([(region, assoc_comments[idx])])
            else:
                import_section_regions[-1].append((region, assoc_comments[idx]))

        for import_section_region in reversed(import_section_regions):
            section_content = self.view.substr(sublime.Region(
                import_section_region[0][0].begin(),
                import_section_region[-1][0].end()),
            )
            section_assoc_comments = [assoc_comment for _, assoc_comment in import_section_region]

            # TODO: assume that section_content contains only import statements
            # TODO: ast.parse will not take into account comments (i.e. all comments will be gone)
            try:
                tree = ast.parse(section_content)
            except SyntaxError as e:
                raise ValueError(f'Failed to parse import section: {e}')
            except Exception as e:
                raise ValueError(f'Failed to parse import section: {e}')

            for node in tree.body:
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    raise ValueError(f'Expected node to be an import or import from statement, got: {ast.dump(node)}')
                node.names = sorted(node.names, key=lambda alias: alias.name)

            # sort import statements
            tree.body, section_assoc_comments = zip(*sorted(zip(tree.body, section_assoc_comments), key=cmp_to_key(node_cmp)))

            # remove duplicates
            new_body = []
            new_section_assoc_comments = []
            for idx in range(len(tree.body)):
                if idx == 0 or ast.dump(tree.body[idx]) != ast.dump(tree.body[idx - 1]):
                    new_body.append(tree.body[idx])
                    new_section_assoc_comments.append(section_assoc_comments[idx])
            tree.body = new_body
            section_assoc_comments = new_section_assoc_comments

            sorted_section_content = unparse_imports(tree, section_assoc_comments)
            self.view.replace(
                edit,
                sublime.Region(import_section_region[0][0].begin(), import_section_region[-1][0].end()),
                sorted_section_content,
            )

    def line_content(self, row: int, full_line: bool = False) -> str:
        if full_line:
            line = self.view.full_line(self.view.text_point(row, 0))
        else:
            line = self.view.line(self.view.text_point(row, 0))
        return self.view.substr(line)

    def starts_with_magic_var(self, line: str) -> bool:
        magic_vars = [
            '__all__',
        ]
        for magic_var in magic_vars:
            if line.startswith(magic_var):
                return True
        return False

def unparse_imports(tree: ast.Module, assoc_comments: List[Optional[str]], tab_size: int = 4) -> str:
    source = []
    tabs = " " * tab_size

    wrap_limits = [
        {'num_aliases': 2, 'limit': 76},
        {'num_aliases': 3, 'limit': 72},
        {'num_aliases': 4, 'limit': 64},
        {'num_aliases': 5, 'limit': 56},
        {'num_aliases': 6, 'limit': 44},
        {'num_aliases': 7, 'limit': -1},
    ]
    assert len(tree.body) == len(assoc_comments)
    for idx, node in enumerate(tree.body):
        if isinstance(node, ast.Import):
            prefix = 'import '
        elif isinstance(node, ast.ImportFrom):
            prefix = f'from {node.module} import '
        else:
            raise ValueError(f'Expected node to be an import or import from statement, got: {ast.dump(node)}')
        aliases = []
        for alias in node.names:
            if alias.asname:
                aliases.append(f'{alias.name} as {alias.asname}')
            else:
                aliases.append(alias.name)

        all_aliases = ', '.join(aliases)
        total_length = len(all_aliases) + len(prefix)
        will_wrap = False
        for wrap_limit in wrap_limits:
            if len(node.names) >= wrap_limit['num_aliases'] and total_length > wrap_limit['limit']:
                will_wrap = True
                break
        if will_wrap:
            prefix += f'(\n{tabs}'
            all_aliases = all_aliases.replace(', ', f',\n{tabs}')
            all_aliases += ',\n)'
        if assoc_comments[idx] is not None:
            all_aliases += '  ' + assoc_comments[idx]
        source.append(prefix + all_aliases)
    return '\n'.join(source)

def node_cmp(lhs, rhs) -> int:
    lhs, rhs = lhs[0], rhs[0]
    if not isinstance(lhs, (ast.Import, ast.ImportFrom)):
        raise ValueError(f'Expected lhs to be an import or import from statement, got: {ast.dump(lhs)}')
    if not isinstance(rhs, (ast.Import, ast.ImportFrom)):
        raise ValueError(f'Expected lhs to be an import or import from statement, got: {ast.dump(rhs)}')

    if isinstance(lhs, ast.Import) and isinstance(rhs, ast.Import):
        if lhs.names[0].name < rhs.names[0].name:
            return -1
        return 1
    elif isinstance(lhs, ast.ImportFrom) and isinstance(rhs, ast.ImportFrom):
        if lhs.module != rhs.module:
            if lhs.module < rhs.module:
                return -1
            return 1
        else:
            lhs_names = [alias.name for alias in lhs.names]
            rhs_names = [alias.name for alias in rhs.names]
            if lhs_names < rhs_names:
                return -1
            return 1
    else:
        return -1 if isinstance(lhs, ast.Import) else 1

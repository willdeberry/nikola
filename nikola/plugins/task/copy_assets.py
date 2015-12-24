# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Copy theme assets into output."""

from __future__ import unicode_literals

import io
import os

from nikola.plugin_categories import Task
from nikola import utils


class CopyAssets(Task):
    """Copy theme assets into output."""

    name = "copy_assets"

    def gen_tasks(self):
        """Create tasks to copy the assets of the whole theme chain.

        If a file is present on two themes, use the version
        from the "youngest" theme.
        """
        kw = {
            "themes": self.site.THEMES,
            "files_folders": self.site.config['FILES_FOLDERS'],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "code_color_scheme": self.site.config['CODE_COLOR_SCHEME'],
            "code.css_selectors": 'pre.code',
            "code.css_head": '/* code.css file generated by Nikola */\n',
            "code.css_close": "\ntable.codetable { width: 100%;} td.linenos {text-align: right; width: 4em;}\n",
        }
        tasks = {}
        code_css_path = os.path.join(kw['output_folder'], 'assets', 'css', 'code.css')
        code_css_input = utils.get_asset_path('assets/css/code.css',
                                              themes=kw['themes'],
                                              files_folders=kw['files_folders'], output_dir=None)
        yield self.group_task()

        for theme_name in kw['themes']:
            src = os.path.join(utils.get_theme_path(theme_name), 'assets')
            dst = os.path.join(kw['output_folder'], 'assets')
            for task in utils.copy_tree(src, dst):
                if task['name'] in tasks:
                    continue
                tasks[task['name']] = task
                task['uptodate'] = [utils.config_changed(kw, 'nikola.plugins.task.copy_assets')]
                task['basename'] = self.name
                if code_css_input:
                    if 'file_dep' not in task:
                        task['file_dep'] = []
                    task['file_dep'].append(code_css_input)
                yield utils.apply_filters(task, kw['filters'])

        # Check whether or not there is a code.css file around.
        if not code_css_input:
            def create_code_css():
                from pygments.formatters import get_formatter_by_name
                formatter = get_formatter_by_name('html', style=kw["code_color_scheme"])
                utils.makedirs(os.path.dirname(code_css_path))
                with io.open(code_css_path, 'w+', encoding='utf8') as outf:
                    outf.write(kw["code.css_head"])
                    outf.write(formatter.get_style_defs(kw["code.css_selectors"]))
                    outf.write(kw["code.css_close"])

            if os.path.exists(code_css_path):
                with io.open(code_css_path, 'r', encoding='utf-8') as fh:
                    testcontents = fh.read(len(kw["code.css_head"])) == kw["code.css_head"]
            else:
                testcontents = False

            task = {
                'basename': self.name,
                'name': code_css_path,
                'targets': [code_css_path],
                'uptodate': [utils.config_changed(kw, 'nikola.plugins.task.copy_assets'), testcontents],
                'actions': [(create_code_css, [])],
                'clean': True,
            }
            yield utils.apply_filters(task, kw['filters'])

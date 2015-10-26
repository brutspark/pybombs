#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
""" PyBOMBS command: install """

from pybombs.commands import CommandBase
from pybombs import packagers
from pybombs import dep_manager
from pybombs import recipe

class Rebuild(CommandBase):
    """ Rebuild a previously installed source package """
    cmds = {
        'rebuild': 'Rebuild an installed package',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'install'
        """
        parser.add_argument(
                'packages',
                help="List of packages to install",
                action='append',
                default=[],
                nargs='*'
        )
        parser.add_argument(
                '--print-tree',
                help="Print dependency tree",
                action='store_true',
        )
        parser.add_argument(
                '--deps',
                help="Also rebuild dependencies",
                action='store_true',
        )
        parser.add_argument(
                '-c', '--clean',
                help="Run a `make clean' (or equivalent) command before rebuilding from source.",
                action='store_true',
        )
        parser.add_argument(
                '-n', '--nuke-build',
                help="Nuke build directory before rebuilding from source.",
                action='store_true',
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=True,
                require_prefix=True,
                require_inventory=True,
        )
        self.pm = packagers.source.Source()
        self.args.packages = args.packages[0]
        if len(self.args.packages) == 0:
            self.args.packages = self.inventory.get_packages()

    def run(self):
        """ Go, go, go! """
        ### Sanity checks
        for pkg in self.args.packages:
            if not self.pm.installed(recipe.get_recipe(pkg)):
                self.log.error("Package {0} is not installed into current prefix. Aborting.".format(pkg))
                exit(1)
        ### Make install tree
        rb_tree = dep_manager.DepManager().make_dep_tree(
            self.args.packages,
            lambda x: bool(
                (x in self.args.packages) or \
                (self.args.deps and self.pm.installed(recipe.get_recipe(x)))
            )
        )
        self.log.debug("Install tree:")
        if self.log.getEffectiveLevel() <= 20 or self.args.print_tree:
            rb_tree.pretty_print()
        ### Recursively rebuild, starting at the leaf nodes
        while not rb_tree.empty():
            pkg = rb_tree.pop_leaf_node()
            rec = recipe.get_recipe(pkg)
            self.log.info("Rebuilding package: {0}".format(pkg))
            if not self.pm.rebuild(
                rec,
                make_clean=self.args.clean,
                nuke_builddir=self.args.nuke_build
            ):
                self.log.error("Error rebuilding package {0}. Aborting.".format(pkg))
                exit(1)
            self.log.info("Rebuild successful.")


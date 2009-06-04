# PiTiVi , Non-linear video editor
#
#       tests/test_projectmanager.py
#
# Copyright (c) 2009, Alessandro Decina <alessandro.d@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from unittest import TestCase

from pitivi.projectmanager import ProjectManager
from pitivi.formatters.base import Formatter, \
        FormatterError, FormatterLoadError

class ProjectManagerListener(object):
    def __init__(self, manager):
        self.manager = manager
        self.connectToProjectManager(self.manager)
        self._reset()

    def _reset(self):
        self.signals = []

    def connectToProjectManager(self, manager):
        for signal in ("new-project-loading", "new-project-loaded",
            "new-project-failed", "missing-uri"):
            self.manager.connect(signal, self._recordSignal, signal)

    def _recordSignal(self, *args):
        signal = args[-1]
        args = args[1:-1]
        self.signals.append((signal, args))


class TestProjectManager(TestCase):
    def setUp(self):
        self.manager = ProjectManager()
        self.listener = ProjectManagerListener(self.manager)
        self.signals = self.listener.signals

    def testLoadProjectFailedUnknownFormat(self):
        """
        Check that new-project-failed is emitted when we don't have a suitable
        formatter.
        """
        uri = "file:///Untitled.meh"
        self.manager.loadProject(uri)
        self.failUnlessEqual(len(self.signals), 2)

        # loading
        name, args = self.signals[0]
        self.failUnlessEqual(args[0], uri)

        # failed
        name, args = self.signals[1]
        self.failUnlessEqual(name, "new-project-failed")
        signalUri, exception = args
        self.failUnlessEqual(uri, signalUri)
        self.failUnless(isinstance(exception, FormatterLoadError))

    def testLoadProjectFailedCloseCurrent(self):
        """
        Check that new-project-failed is emited if we can't close the current
        project instance.
        """
        state = {"tried-close": False}
        def close():
            state["tried-close"] = True
            return False
        self.manager.closeRunningProject = close

        uri = "file:///Untitled.xptv"
        self.manager.loadProject(uri)
        self.failUnlessEqual(len(self.signals), 2)

        # loading
        name, args = self.signals[0]
        self.failUnlessEqual(args[0], uri)

        # failed
        name, args = self.signals[1]
        self.failUnlessEqual(name, "new-project-failed")
        signalUri, exception = args
        self.failUnlessEqual(uri, signalUri)
        self.failUnless(isinstance(exception, FormatterLoadError))
        self.failUnless(state["tried-close"])

    def testLoadProjectFailedProxyFormatter(self):
        """
        Check that new-project-failed is proxied when a formatter emits it.
        """
        class FailFormatter(Formatter):
            def _validateUri(self, uri):
                pass

            def _parse(self, location, project=None):
                raise FormatterError()
        self.manager._getFormatterForUri = lambda uri: FailFormatter()

        uri = "file:///Untitled.xptv"
        self.manager.loadProject(uri)
        self.failUnlessEqual(len(self.signals), 2)

        # loading
        name, args = self.signals[0]
        self.failUnlessEqual(args[0], uri)

        # failed
        name, args = self.signals[1]
        self.failUnlessEqual(name, "new-project-failed")
        signalUri, exception = args
        self.failUnlessEqual(uri, signalUri)
        self.failUnless(isinstance(exception, FormatterError))

    def testLoadProjectMissingUri(self):
        class FailFormatter(Formatter):
            def _validateUri(self, uri):
                pass

            def _parse(self, location, project=None):
                pass

            def _getSources(self):
                # this will emit missing-uri
                self.validateSourceURI("file:///icantpossiblyexist")
                return []

            def _fillTimeline(self):
                pass
        self.manager._getFormatterForUri = lambda uri: FailFormatter()

        uri = "file:///Untitled.xptv"
        self.manager.loadProject(uri)
        self.failUnlessEqual(len(self.signals), 3)

        # loading
        name, args = self.signals[0]
        self.failUnlessEqual(args[0], uri)

        # failed
        name, args = self.signals[1]
        self.failUnlessEqual(name, "missing-uri")
        formatter, signalUri = args
        self.failUnlessEqual(signalUri, "file:///icantpossiblyexist")


    def testLoadProjectLoaded(self):
        class FailFormatter(Formatter):
            def _validateUri(self, uri):
                pass

            def _parse(self, location, project=None):
                pass

            def _getSources(self):
                return []

            def _fillTimeline(self):
                pass
        self.manager._getFormatterForUri = lambda uri: FailFormatter()

        uri = "file:///Untitled.xptv"
        self.manager.loadProject(uri)
        self.failUnlessEqual(len(self.signals), 2)

        # loading
        name, args = self.signals[0]
        self.failUnlessEqual(args[0], uri)

        # failed
        name, args = self.signals[1]
        self.failUnlessEqual(name, "new-project-loaded")
        project = args[0]
        self.failUnlessEqual(uri, project.uri)


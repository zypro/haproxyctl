# pylint: disable=locally-disabled, too-few-public-methods, no-self-use, invalid-name
"""cmds.py - Implementations of the different HAProxy commands"""

import re

class Cmd(object):
    """Cmd - Command base class"""

    p_args = []
    args = {}
    cmdTxt = ""
    helpTxt = ""

    # pylint: disable=unused-argument
    def __init__(self, *args, **kwargs):
        """Argument to the command are given in kwargs only. We ignore *args."""

        self.args = kwargs
        if not all([a in kwargs.keys() for a in self.p_args]):
            raise Exception("Wrong number of arguments. Required arguments are " +
                            self.WhatArgs())

    def WhatArgs(self):
        """Returns a formatted string of arguments to this command."""
        return ",".join(self.p_args)

    @classmethod
    def getHelp(cls):
        """Get formatted help string for this command."""
        txtArgs = ",".join(cls.p_args)

        if not txtArgs:
            txtArgs = "None"
        return " ".join((cls.helpTxt, "Arguments: %s" % txtArgs))

    def getCmd(self):
        """Gets the command line for this command.
        The default behavior is to apply the args dict to cmdTxt
        """
        return self.cmdTxt % self.args

    def getResult(self, res):
        """Returns raw results gathered from HAProxy"""
        return res

    def getResultObj(self, res):
        """Returns refined output from HAProxy, packed inside a Python obj i.e. a dict()"""
        return res

class _ableServer(Cmd):
    """Base class for enable/disable commands"""

    cmdTxt = "server %(backend)s/%(server)s\r\n"
    p_args = ["backend", "server"]
    switch = ""

    def getCmd(self):
        if not self.switch:
            raise Exception("No action specified")
        cmdTxt = " ".join((self.switch, self.cmdTxt % self.args))
        return cmdTxt

class disableServer(_ableServer):
    """Disable backend/server command."""
    switch = "disable"
    helpTxt = "Disables given backend/server"

class enableServer(_ableServer):
    """Enable backend/server command."""
    switch = "enable"
    helpTxt = "Enables given backend/server"

class setWeight(Cmd):
    """Set weight command."""
    cmdTxt = "set weight %(backend)s/%(server)s %(weight)s\r\n"
    p_args = ['backend', 'server', 'weight']
    helpTxt = "Set weight for a given backend/server."

class getWeight(Cmd):
    """Get weight command."""
    cmdTxt = "get weight %(backend)s/%(server)s\r\n"
    p_args = ['backend', 'server']
    helpTxt = "Get weight for a given backend/server."

class showErrors(Cmd):
    """Show errors HAProxy command."""
    cmdTxt = "show errors\r\n"
    helpTxt = "Shows errors on HAProxy instance."

    def getResultObj(self, res):
        return res.split('\n')

class setServerAgent(Cmd):
    """Set server agent command."""
    cmdTxt = "set server %(backend)s/%(server)s agent %(value)s\r\n"
    p_args = ['backend', 'server', 'value']
    helpTxt = "Force a server's agent to a new state."

class setServerHealth(Cmd):
    """Set server health command."""
    cmdTxt = "set server %(backend)s/%(server)s health %(value)s\r\n"
    p_args = ['backend', 'server', 'value']
    helpTxt = "Force a server's health to a new state."

class setServerState(Cmd):
    """Set server state command."""
    cmdTxt = "set server %(backend)s/%(server)s state %(value)s\r\n"
    p_args = ['backend', 'server', 'value']
    helpTxt = "Force a server's administrative state to a new state."

class showFBEnds(Cmd):
    """Base class for getting a listing Frontends and Backends"""
    switch = ""
    cmdTxt = "show stat\r\n"

    def getResult(self, res):
        return "\n".join(self._getResult(res))

    def getResultObj(self, res):
        return self._getResult(res)

    def _getResult(self, res):
        """Show Frontend/Backends. To do this, we extract info from
           the stat command and filter out by a specific
           switch (FRONTEND/BACKEND)"""

        if not self.switch:
            raise Exception("No action specified")

        result = []
        lines = res.split('\n')
        cl = re.compile("^[^,].+," + self.switch.upper() + ",.*$")

        for e in lines:
            me = re.match(cl, e)
            if me:
                result.append(e.split(",")[0])
        return result

class showFrontends(showFBEnds):
    """Show frontends command."""
    switch = "frontend"
    helpTxt = "List all Frontends."

class showBackends(showFBEnds):
    """Show backends command."""
    switch = "backend"
    helpTxt = "List all Backends."

class showInfo(Cmd):
    """Show info HAProxy command"""
    cmdTxt = "show info\r\n"
    helpTxt = "Show info on HAProxy instance."

    def getResultObj(self, res):
        resDict = {}
        for line in res.split('\n'):
            k, v = line.split(':')
            resDict[k] = v

        return resDict

class showSessions(Cmd):
    """Show sess HAProxy command"""
    cmdTxt = "show sess\r\n"
    helpTxt = "Show HAProxy sessions."

    def getResultObj(self, res):
        return res.split('\n')

class baseStat(Cmd):
    """Base class for stats commands."""

    def getCols(self, res):
        """Get columns from stats output."""
        mobj = re.match("^#(?P<columns>.*)$", res, re.MULTILINE)

        if mobj:
            return dict((a, i) for i, a in enumerate(mobj.groupdict()['columns'].split(',')))
        raise Exception("Could not parse columns from HAProxy output")

class listServers(baseStat):
    """Show servers in the given backend"""

    p_args = ['backend']
    cmdTxt = "show stat\r\n"
    helpTxt = "Lists servers in the given backend"

    def getResult(self, res):
        return "\n".join(self.getResultObj(res))

    def getResultObj(self, res):
        servers = []
        cols = self.getCols(res)

        for line in res.split('\n'):
            if line.startswith(self.args['backend'] + ','):
                # Lines for server start with the name of the
                # backend.

                outCols = line.split(',')
                if outCols[cols['svname']] != 'BACKEND':
                    servers.append(" " .join(("Name: %s" % outCols[cols['svname']],
                                              "Status: %s" % outCols[cols['status']],
                                              "Weight: %s" %  outCols[cols['weight']],
                                              "bIn: %s" % outCols[cols['bin']],
                                              "bOut: %s" % outCols[cols['bout']])))

        return servers

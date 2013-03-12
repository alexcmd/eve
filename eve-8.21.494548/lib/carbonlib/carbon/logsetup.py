#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\logsetup.py
import logging
LGINFO = 1
LGPERF = 32
LGWARN = 2
LGERR = 4
LGFATAL = 8
LOG_MAXMESSAGE = 252
INDENT_PREFIX = '  '
_hasBeenInit = False

def Init():
    global _hasBeenInit
    if _hasBeenInit:
        return
    _hasBeenInit = True
    try:
        from blue import LogChannel
        SPLITMESSAGES = False
    except ImportError:
        LogChannel = None
        SPLITMESSAGES = True

    if LogChannel is None:
        try:
            from _logclient import LogChannel
        except ImportError:
            LogChannel = None

    levelMap = {logging.CRITICAL: LGFATAL,
     logging.ERROR: LGERR,
     logging.WARNING: LGWARN,
     logging.INFO: LGPERF,
     logging.DEBUG: LGINFO,
     logging.NOTSET: LGINFO}
    if LogChannel is None:
        logging.error('Could not import a LogChannel for LogServer! No LogServer handler added for this process')
        return

    class LogServerHandler(logging.Handler):

        def __init__(self):
            super(LogServerHandler, self).__init__()
            self.channels = {}

        def emit(self, record):
            try:
                if record.name not in self.channels:
                    if '.' in record.name:
                        channel, object = record.name.split('.', 1)
                    else:
                        channel, object = record.name, 'General'
                    self.channels[record.name] = LogChannel(channel, object)
                severity = levelMap.get(record.levelno, levelMap[logging.INFO])
                ch = self.channels[record.name]
                msg = self.format(record)
                if SPLITMESSAGES:
                    splitter = lambda s, p: [ s[i:i + p] for i in range(0, len(s), p) ]
                    indent = ''
                    for line in msg.split('\n'):
                        if line:
                            for linesegment in splitter(line, LOG_MAXMESSAGE - len(INDENT_PREFIX)):
                                ch.Log(indent + linesegment, severity)
                                indent = INDENT_PREFIX

                else:
                    ch.Log(msg, severity)
            except Exception:
                self.handleError(record)

    logserver = LogServerHandler()
    logging.root.addHandler(logserver)
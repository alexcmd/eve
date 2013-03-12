#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/modules/telemetrypanel.py
import blue
import uthread
import uicls
import uiutil
import uiconst
import base

class TelemetryPanel(uicls.Window):
    __guid__ = 'form.TelemetryPanel'
    default_caption = 'Telemetry Panel'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        if hasattr(self, 'SetTopparentHeight'):
            self.SetTopparentHeight(0)
            self.container = uicls.Container(parent=self.sr.main, align=uiconst.TOALL)
        else:
            self.container = uicls.Container(parent=self.sr.content, align=uiconst.TOALL)
        self.optionsContainer = uicls.Container(parent=self.container, align=uiconst.TOTOP, height=32)
        self.cppCaptureChk = uicls.Checkbox(parent=self.optionsContainer, text='C++ capture', checked=blue.statistics.isCppCaptureEnabled, callback=self._OnCppCaptureChk, align=uiconst.TOTOP)
        self.buttonContainer = uicls.GridContainer(parent=self.container, align=uiconst.TOALL, columns=2, rows=2)
        self.startBtn = uicls.Button(parent=self.buttonContainer, align=uiconst.TOALL, label='Start', func=self._Start)
        self.stopBtn = uicls.Button(parent=self.buttonContainer, align=uiconst.TOALL, label='Stop', func=self._Stop)
        self.pauseBtn = uicls.Button(parent=self.buttonContainer, align=uiconst.TOALL, label='Pause', func=self._Pause)
        self.resumeBtn = uicls.Button(parent=self.buttonContainer, align=uiconst.TOALL, label='Resume', func=self._Resume)
        uthread.new(self._CheckStatus)

    def _OnCppCaptureChk(self, checkbox):
        blue.statistics.isCppCaptureEnabled = checkbox.GetValue()

    def _Start(self, args):
        print 'Starting Telemetry'
        blue.statistics.StartTelemetry('localhost')

    def _Stop(self, args):
        print 'Stopping Telemetry'
        blue.statistics.StopTelemetry()

    def _Pause(self, args):
        print 'Pausing Telemetry'
        blue.statistics.PauseTelemetry()

    def _Resume(self, args):
        print 'Resuming Telemetry'
        blue.statistics.ResumeTelemetry()

    def _CheckStatus(self):
        while not self.destroyed:
            self.cppCaptureChk.SetChecked(blue.statistics.isCppCaptureEnabled, report=False)
            if blue.statistics.isTelemetryConnected:
                self.startBtn.Disable()
                self.stopBtn.Enable()
                if blue.statistics.isTelemetryPaused:
                    self.pauseBtn.Disable()
                    self.resumeBtn.Enable()
                else:
                    self.pauseBtn.Enable()
                    self.resumeBtn.Disable()
            else:
                self.startBtn.Enable()
                self.stopBtn.Disable()
                self.pauseBtn.Disable()
                self.resumeBtn.Disable()
            blue.synchro.SleepWallclock(500)
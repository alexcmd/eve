#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\eve\common\lib\autoexec_proxy.py
import autoexec_proxy_core
import blue
import eveLog
servicesToRun = ['counter',
 'tcpRawProxyService',
 'http',
 'http2',
 'machoNet',
 'objectCaching',
 'debug',
 'sessionMgr',
 'ramProxy',
 'clientStatLogger',
 'alert',
 'processHealth',
 'dustContentStreamingProxyMgr',
 'lscProxy',
 'API',
 'battleInitialization']
import eveLocalization
if boot.region == 'optic':
    eveLocalization.SetTimeDelta(28800)
servicesToBlock = ['DB2']
autoexec_proxy_core.StartProxy(servicesToRun, servicesToBlock=servicesToBlock, serviceManagerClass='EveServiceManager')
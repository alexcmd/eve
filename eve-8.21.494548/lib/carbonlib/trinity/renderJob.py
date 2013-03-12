#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\trinity\renderJob.py
import decometaclass
import trinity
import blue

class RenderJob(object):
    __cid__ = 'trinity.TriRenderJob'
    __metaclass__ = decometaclass.BlueWrappedMetaclass

    def __init__(self):
        self.cancelled = False

    def ScheduleOnce(self):
        self.status = trinity.RJ_INIT
        trinity.renderJobs.once.append(self)

    def ScheduleChained(self):
        trinity.renderJobs.chained.append(self)

    def CancelChained(self):
        self.cancelled = True
        if self in trinity.renderJobs.chained:
            trinity.renderJobs.chained.remove(self)

    def ScheduleRecurring(self, scheduledRecurring = None, insertFront = False):
        if scheduledRecurring is None:
            scheduledRecurring = trinity.renderJobs.recurring
        if insertFront == False:
            scheduledRecurring.append(self)
        else:
            scheduledRecurring.insert(0, self)

    def UnscheduleRecurring(self, scheduledRecurring = None):
        if scheduledRecurring is None:
            scheduledRecurring = trinity.renderJobs.recurring
        if self in scheduledRecurring:
            scheduledRecurring.remove(self)

    def WaitForFinish(self):
        while not (self.status == trinity.RJ_DONE or self.status == trinity.RJ_FAILED or self.cancelled):
            blue.synchro.Yield()


def _GetRenderJobCreationClosure(functionName, doc, classThunker):

    def CreateStep(self, *args):
        step = classThunker(*args)
        self.steps.append(step)
        return step

    CreateStep.__doc__ = doc
    CreateStep.__name__ = functionName
    return CreateStep


for className, desc in trinity.GetClassInfo().iteritems():
    if className.startswith('TriStep'):
        setattr(RenderJob, className[7:], _GetRenderJobCreationClosure(className[7:], desc[3].get('__init__', 'Create a %s render step and add it to the render job' % className), getattr(trinity, className)))

def CreateRenderJob(name = None):
    job = RenderJob()
    if name:
        job.name = name
    return job


class RenderJobs(object):
    __cid__ = 'trinity.Tr2RenderJobs'
    __metaclass__ = decometaclass.BlueWrappedMetaclass

    def __init__(self):
        pass

    def UnscheduleByName(self, name):
        for rj in self.recurring:
            if rj.name == name:
                self.recurring.remove(rj)
                return True

        return False

    def FindByName(self, name):
        for rj in self.recurring:
            if rj.name == name:
                return rj

    def FindStepByName(self, name):

        def FindInJob(rj):
            for step in rj.steps:
                if step.name == name:
                    return step

        for rj in self.recurring:
            ret = FindInJob(rj)
            if ret is not None:
                return ret

    def FindScenes(self, sceneType = trinity.Tr2InteriorScene, filter = lambda x: True):
        results = set({})

        def RecursiveSearch(job):
            for step in job.steps:
                if hasattr(step, 'object') and type(step.object) is sceneType and filter(step.object):
                    results.add(step.object)
                    return
                if type(step) is trinity.TriStepRunJob:
                    RecursiveSearch(step.job)

        for job in trinity.renderJobs.recurring:
            RecursiveSearch(job)

        return results
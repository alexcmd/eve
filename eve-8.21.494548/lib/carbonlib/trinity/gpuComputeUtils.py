#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\trinity\gpuComputeUtils.py
import trinity
import blue

def CreatePrefixSumJob(inputUav, outputUav, debugging = False, allowRecursion = True, folder = 'prefixsum'):
    NUM_ELEM = inputUav.numElements
    if NUM_ELEM & 3:
        return None
    NUM_THREAD_PER_BLOCK = 256
    NUM_BLOCKS_PHASE1 = max(1, ((NUM_ELEM + 3) / 4 + NUM_THREAD_PER_BLOCK - 1) / NUM_THREAD_PER_BLOCK)
    fxPath = 'res:/graphics/effect/compute/' + folder + '/'
    phase1fx = trinity.Tr2Effect()
    phase1fx.effectFilePath = fxPath + 'phase1.fx'
    recurse = allowRecursion and NUM_BLOCKS_PHASE1 >= 1024 and NUM_BLOCKS_PHASE1 % 4 == 0
    if not recurse:
        phase2fx = trinity.Tr2Effect()
        phase2fx.effectFilePath = fxPath + 'phase2.fx'
    phase3fx = trinity.Tr2Effect()
    phase3fx.effectFilePath = fxPath + 'phase3.fx'
    blue.resMan.Wait()
    if debugging:
        phase1fx.effectResource.Reload()
        if not recurse:
            phase2fx.effectResource.Reload()
        phase3fx.effectResource.Reload()
    blockOffsets = trinity.Tr2UavBuffer(NUM_BLOCKS_PHASE1, trinity.PIXEL_FORMAT.R32_UINT)
    blockOffsets.name = 'blockOffsets'
    phase1 = trinity.TriStepRunComputeShader(phase1fx, NUM_BLOCKS_PHASE1, 1)
    if recurse:
        summedBlockOffsets = trinity.Tr2UavBuffer(NUM_BLOCKS_PHASE1, trinity.PIXEL_FORMAT.R32_UINT)
        phase2 = CreatePrefixSumJob(blockOffsets, summedBlockOffsets, debugging)
        phase2 = trinity.TriStepRunJob(phase2)
    else:
        phase2 = trinity.TriStepRunComputeShader(phase2fx, 1, 1)
    phase3 = trinity.TriStepRunComputeShader(phase3fx, NUM_BLOCKS_PHASE1, 1)
    if debugging:
        phase1.logDispatchTime = True
        if not recurse:
            phase2.logDispatchTime = True
        phase3.logDispatchTime = True
    phase1.name = 'phase1'
    phase2.name = 'phase2'
    phase3.name = 'phase3'
    input4 = trinity.Tr2UavBuffer()
    input4.CreateAlias(inputUav, trinity.PIXEL_FORMAT.R32G32B32A32_UINT)
    input4.name = 'input4'
    rj = trinity.CreateRenderJob('PrefixSum')
    phase1.SetSrvBuffer(0, input4)
    phase1.SetUavBuffer(1, blockOffsets)
    phase1.autoClearUav = False
    phase1.autoResetUav = True
    if not recurse:
        phase2.SetUavBuffer(1, blockOffsets)
        phase2.autoClearUav = False
        phase2.autoResetUav = True
    phase3.SetSrvBuffer(0, input4)
    phase3.SetUavBuffer(1, blockOffsets if not recurse else summedBlockOffsets)
    phase3.SetUavBuffer(2, outputUav)
    phase3.autoClearUav = False
    phase3.autoResetUav = True
    rj.steps.append(phase1)
    rj.steps.append(phase2)
    rj.steps.append(phase3)
    return rj


def CreateRadixSortJob(inOutUav, bitSize = 32, debugging = False):
    NUM_ELEM = inOutUav.numElements
    NUM_BLOCKS_PHASE1 = NUM_ELEM / 512
    NUM_BLOCKS_PHASE21 = max(1, (NUM_BLOCKS_PHASE1 * 16 + 31) / 32)
    fxPath = 'res:/graphics/effect/compute/sort/'
    phase1fx = trinity.Tr2Effect()
    phase1fx.effectFilePath = fxPath + 'sort_phase1.fx'
    phase21fx = trinity.Tr2Effect()
    phase21fx.effectFilePath = fxPath + 'sort_phase21.fx'
    phase23fx = trinity.Tr2Effect()
    phase23fx.effectFilePath = fxPath + 'sort_phase23.fx'
    phase3fx = trinity.Tr2Effect()
    phase3fx.effectFilePath = fxPath + 'sort_phase3.fx'
    blue.resMan.Wait()
    trinity.GetVariableStore().RegisterVariable('gpuComputeSortThreadData', (0.0, 0.0, 0.0, 0.0))
    if debugging:
        for fx in [phase1fx,
         phase21fx,
         phase23fx,
         phase3fx]:
            fx.effectResource.Reload()

    phase1 = trinity.TriStepRunComputeShader(phase1fx, NUM_BLOCKS_PHASE1, 1)
    phase1.name = 'phase1'
    phase21 = trinity.TriStepRunComputeShader(phase21fx, NUM_BLOCKS_PHASE21, 1)
    phase21.name = 'phase21'
    phase23 = trinity.TriStepRunComputeShader(phase23fx, NUM_BLOCKS_PHASE21, 1)
    phase23.name = 'phase23'
    phase3 = trinity.TriStepRunComputeShader(phase3fx, NUM_BLOCKS_PHASE1, 1)
    phase3.name = 'phase3'
    input4 = trinity.Tr2UavBuffer()
    input4.CreateAlias(inOutUav, trinity.PIXEL_FORMAT.R32G32B32A32_UINT)
    input4.name = 'input4'
    output4 = trinity.Tr2UavBuffer((NUM_ELEM + 3) / 4, trinity.PIXEL_FORMAT.R32G32B32A32_UINT)
    output4.name = 'output4'
    allHistogram = trinity.Tr2UavBuffer(NUM_BLOCKS_PHASE1 * 16, trinity.PIXEL_FORMAT.R32_UINT)
    allHistogram.name = 'allHistogram'
    bucketStartPos = trinity.Tr2UavBuffer(NUM_BLOCKS_PHASE1 * 16, trinity.PIXEL_FORMAT.R32_UINT)
    bucketStartPos.name = 'bucketStartPos'

    def RoundUpTo4(n):
        n = n + 3
        n = n / 4
        return n * 4

    offsets = trinity.Tr2UavBuffer(RoundUpTo4(NUM_BLOCKS_PHASE21), trinity.PIXEL_FORMAT.R32_UINT)
    offsets.name = 'offsets'
    offsetsSummed = trinity.Tr2UavBuffer(RoundUpTo4(NUM_BLOCKS_PHASE21), trinity.PIXEL_FORMAT.R32_UINT)
    offsetsSummed.name = 'offsetsSummed'
    if False:
        phase0 = trinity.TriStepRunComputeShader(phase1fx, 0, 0)
        phase0.name = 'phase0'
        phase0.SetUavBuffer(2, offsetsSummed)
        phase0.SetUavBuffer(3, offsets)
        phase0.SetUavBuffer(4, bucketStartPos)
        phase0.autoClearUav = True
        phase0.autoResetUav = True
    phase1.SetSrvBuffer(0, input4)
    phase1.SetUavBuffer(1, output4)
    phase1.SetUavBuffer(2, allHistogram)
    phase1.SetUavBuffer(4, bucketStartPos)
    phase1.autoClearUav = False
    phase21.SetUavBuffer(2, allHistogram)
    phase21.SetUavBuffer(3, offsets)
    phase21.autoClearUav = False
    phase23.SetUavBuffer(2, allHistogram)
    phase23.SetUavBuffer(3, offsetsSummed)
    phase23.autoClearUav = False
    phase3.SetSrvBuffer(0, output4)
    phase3.SetUavBuffer(1, inOutUav)
    phase3.SetUavBuffer(2, allHistogram)
    phase3.SetUavBuffer(4, bucketStartPos)
    phase3.autoClearUav = False
    if debugging:
        for phase in [phase1,
         phase21,
         phase23,
         phase3]:
            phase.logDispatchTime = True

    rjPrefixSum = trinity.gpuComputeUtils.CreatePrefixSumJob(offsets, offsetsSummed, debugging)
    rj = trinity.CreateRenderJob('RadixSort')
    for i in xrange(bitSize / 4):
        value = (i * 4,
         0,
         NUM_BLOCKS_PHASE1,
         0)
        rj.SetVariableStore('gpuComputeSortThreadData', value)
        rj.steps.append(phase1)
        rj.steps.append(phase21)
        rj.RunJob(rjPrefixSum)
        rj.steps.append(phase23)
        rj.steps.append(phase3)

    return rj


def CreateCompactJob(inputUav, outputTidUav, outputCountUav, debugging = False, sumCounts = True):
    NUM_ELEM = inputUav.numElements
    NUM_THREAD_PER_BLOCK = 256
    NUM_BLOCKS_PHASE1 = max(1, (NUM_ELEM + NUM_THREAD_PER_BLOCK - 1) / NUM_THREAD_PER_BLOCK)
    rj = trinity.CreateRenderJob('Compact')
    intermediate = trinity.Tr2UavBuffer(NUM_ELEM, trinity.PIXEL_FORMAT.R32_UINT)
    intermediate.name = 'intermediate'
    sumJob = trinity.gpuComputeUtils.CreatePrefixSumJob(inputUav, intermediate, debugging, folder='prefixSumCompaction')
    if sumJob.steps[-1].name != 'phase3':
        return None
    dispatchParams = trinity.Tr2UavBuffer()
    dispatchParams.CreateEx(3, trinity.PIXEL_FORMAT.R32_UINT, trinity.EX_FLAG.DRAW_INDIRECT)
    dispatchParams.name = 'dispatchParams'
    sumJob.steps[-1].SetUavBuffer(3, dispatchParams)
    rj.RunJob(sumJob)
    if sumCounts:
        size = outputCountUav.numElements
        size = max(512, (size + 511) / 512 * 512)
        intermediateCount = trinity.Tr2UavBuffer(size, trinity.PIXEL_FORMAT.R32_UINT)
        intermediateCount.name = 'intermediateCount'
    fxPath = 'res:/graphics/effect/compute/compaction/'
    phase1fx = trinity.Tr2Effect()
    phase1fx.effectFilePath = fxPath + 'phase1.fx'
    blue.resMan.Wait()
    phase1 = trinity.TriStepRunComputeShader(phase1fx, NUM_BLOCKS_PHASE1)
    phase1.name = 'phase1'
    if debugging:
        phase1fx.effectResource.Reload()
        phase1.logDispatchTime = True
    phase1.SetSrvBuffer(0, inputUav)
    phase1.SetSrvBuffer(1, intermediate)
    phase1.SetUavBuffer(2, outputTidUav)
    phase1.SetUavBuffer(3, outputCountUav if not sumCounts else intermediateCount)
    phase1.autoClearUav = False
    rj.steps.append(phase1)
    if sumCounts:
        sumJob = trinity.gpuComputeUtils.CreatePrefixSumJob(intermediateCount, outputCountUav, debugging)
        sumJob.steps[0].indirectionBuffer = dispatchParams
        sumJob.steps[2].indirectionBuffer = dispatchParams
        rj.RunJob(sumJob)
    return (rj, intermediate, dispatchParams)
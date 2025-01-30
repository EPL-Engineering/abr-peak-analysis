# -*- coding: utf-8 -*-
"""
Created on Wed Dec  7 15:07:08 2022

@author: kehan
"""

from numpy import array
import numpy as np
from pathlib import Path
import re
import struct
import os

class KParam:
    name = ''
    units = ''
    ptype = 0
    expr = ''
    value = float("NaN")

    def fromBytes(self, bytes, index):
        self.name, index = parseString(bytes, index)
        self.units, index = parseString(bytes, index)
        self.ptype = bytes[index]
        index += 1
        self.expr, index = parseString(bytes, index)
        self.value, index = parseFloat32(bytes, index)
        
        return index
    

class Info:
    name = ''
    description = ''
    paramFile = ''
    fileName = ''
    fileData = ''
    version = ''
    revision = -1
    
    trackNum = -1
    unitNum = -1
    measNum = -1
    runNum = -1
    
    metrics = None
    
    def fromBytes(self, bytes, index):
        
        index = parseIndicator(bytes, index, 'Experiment Info')
        
        self.name, index = parseString(bytes, index)
        self.description, index = parseString(bytes, index)
        self.paramFile, index = parseString(bytes, index)
        self.fileName, index = parseString(bytes, index)
        self.fileData, index = parseString(bytes, index)
        self.version, index = parseString(bytes, index)
        
        self.trackNum, index = parseInt32(bytes, index)
        self.unitNum, index = parseInt32(bytes, index)
        self.measNum, index = parseInt32(bytes, index)
        self.runNum, index = parseInt32(bytes, index)
        
        self.metrics, index = parseKParam(bytes, index)

        p_rev = re.compile('Version [\d]+\.[\d]+\.[\d]+\.([\d]+)')
        self.revision = int(p_rev.search(self.version).group(1))
        print(f'ANECS revision = {self.revision}')
        
        return index


class Equip:
    DACname = ''
    ETname = ''
    numStimChan = -1
    numAtten = -1    
    attenName = []

    def fromBytes(self, bytes, index):
        index = parseIndicator(bytes, index, 'Hardware Configuration')
        
        self.DACname, index = parseString(bytes, index)
        self.ETname, index = parseString(bytes, index)
        self.numStimChan, index = parseInt32(bytes, index)
        self.numAtten, index = parseInt32(bytes, index)
        
        for kc in range(0, self.numStimChan):
            for ka in range(0, self.numAtten):
                att, index = parseString(bytes, index)
                self.attenName.append(att)
        
        return index

class Gate:
    isActive = False
    delay = float("NaN")
    width = float("NaN")
    risefall = float("NaN")

    def fromBytes(self, bytes, index):
        self.isActive, index = parseBoolean(bytes, index)
        self.delay, index = parseFloat32(bytes, index)
        self.width, index = parseFloat32(bytes, index)
        self.risefall, index = parseFloat32(bytes, index)
        return index    

class Level:
    mode = -1
    value = float("NaN")
    expr = ''
    atten = float("NaN")
    reference = float("NaN")

    def fromBytes(self, bytes, index):
        self.mode, index = parseInt32(bytes, index)
        self.value, index = parseFloat32(bytes, index)
        self.expr, index = parseString(bytes, index)
        self.atten, index = parseFloat32(bytes, index)
        self.reference, index = parseFloat32(bytes, index)
        return index    


class StimChannel:
    name = ''
    destination = ''
    waveform = ''
    param = None
    gate = Gate()
    modActive = False
    modType = ''
    modParam = None
    level = Level()

    def fromBytes(self, bytes, index):
        indicator, index = parseString(bytes, index)
        if indicator.startswith('Channel') != True:
            raise Exception('Error reading ANECS data file')
        
        self.name, index = parseString(bytes, index)
        self.destination, index = parseString(bytes, index)
        self.waveform, index = parseString(bytes, index)
        self.param, index = parseKParam(bytes, index)
        index = self.gate.fromBytes(bytes, index)
        self.modType, index = parseString(bytes, index)
        self.modActive, index = parseBoolean(bytes, index)
        self.modParam, index = parseKParam(bytes, index)
        index = self.level.fromBytes(bytes, index)
        return index    

class Stim:
    samplingRate = float("NaN")
    totalDuration = float("NaN")
    numReps = -1
    refreshInterval = float("NaN")
    measTag = ''
    
    channels = []

    def fromBytes(self, bytes, index, numChan):
        index = parseIndicator(bytes, index, 'Stimulus Info')

        self.samplingRate, index = parseFloat32(bytes, index)
        self.totalDuration, index = parseFloat32(bytes, index)
        self.numReps, index = parseInt32(bytes, index)
        self.refreshInterval, index = parseFloat32(bytes, index)
        self.measTag, index = parseString(bytes, index)

        for k in range(0, numChan):
            self.channels.append(StimChannel())
            index = self.channels[k].fromBytes(bytes, index)
        
        return index

class RespChannel:
    isActive = False
    name = ''
    gain = float("NaN")
    useMic = False
    sens = float("NaN")

    def fromBytes(self, bytes, index):
        self.isActive, index = parseBoolean(bytes, index)
        self.name, index = parseString(bytes, index)
        self.gain, index = parseFloat32(bytes, index)
        self.useMic, index = parseBoolean(bytes, index)
        self.sens, index = parseFloat32(bytes, index)
        return index
        
class Resp:
    saveSpikeTimes = False
    saveRawWaveform = False
    saveAvgWaveform = False
    samplingRate = float("NaN")
    channels = []

    def fromBytes(self, bytes, index):
        index = parseIndicator(bytes, index, 'Response Info')

        self.saveSpikeTimes, index = parseBoolean(bytes, index)
        self.saveRawWaveform, index = parseBoolean(bytes, index)
        self.saveAvgWaveform, index = parseBoolean(bytes, index)
        self.samplingRate, index = parseFloat32(bytes, index)
    
        n, index = parseInt32(bytes, index)
        self.channels = [RespChannel() for k in range(n)]
        for k in range(n):
            index = self.channels[k].fromBytes(bytes, index)
            
        return index
    
class Sequence:
    channels = ''
    seqVar = ''
    units = ''
    stepMode = -1
    seqOrder = -1
    startExpr = ''
    start = float("NaN")
    end = float("NaN")
    stepSize = float("NaN")
    nsteps = -1
    setWhich = -1
    
    isOddball = False
    oddballFract = float("NaN")
    standardValue = float("NaN")

    vals = None

    def fromBytes(self, bytes, index, fileFormat):
        index = parseIndicator(bytes, index, 'Sequence')

        self.channels, index = parseString(bytes, index)
        self.seqVar, index = parseString(bytes, index)
        self.units, index = parseString(bytes, index)

        self.stepMode, index = parseInt32(bytes, index)
        self.seqOrder, index = parseInt32(bytes, index)

        self.startExpr, index = parseString(bytes, index)

        self.start, index = parseFloat32(bytes, index)
        self.end, index = parseFloat32(bytes, index)
        self.stepSize, index = parseFloat32(bytes, index)

        self.nsteps, index = parseInt32(bytes, index)
        self.setWhich, index = parseInt32(bytes, index)
        
        self.isOddball, index = parseBoolean(bytes, index)
        self.oddballFract, index = parseFloat32(bytes, index)
        self.standardValue, index = parseInt32(bytes, index)
        
        if fileFormat > 40:
            dummy, index = parseString(bytes, index)
        
        n, index = parseInt32(bytes, index)
        if n > 0:
            valList = [];
            for k in range(n):
                v, index = parseFloat32(bytes, index)
                valList.append(v)
            self.vals = array(valList)
            
        return index
    
class StimCon:
    outer = -1
    inner = -1
    rep = -1
    skip = False
    isOddball = False
    innerVal = float("NaN")
    outerVal = float("NaN")

    def fromBytes(self, bytes, index):
        self.outer, index = parseInt32(bytes, index)
        self.inner, index = parseInt32(bytes, index)
        self.rep, index = parseInt32(bytes, index)
        self.skip, index = parseBoolean(bytes, index)
        self.isOddball, index = parseBoolean(bytes, index)
        self.innerVal, index = parseFloat32(bytes, index)
        self.outerVal, index = parseFloat32(bytes, index)
        return index
        
class StimConList:
    numBlocks = -1
    blockLength = -1
    numInner = -1
    numOuter = -1
    blocks = []
    
    def fromBytes(self, bytes, index):
        index = parseIndicator(bytes, index, 'Stimulus List')
        self.numBlocks, index = parseInt32(bytes, index)
        self.blockLength, index = parseInt32(bytes, index)
        self.numInner, index = parseInt32(bytes, index)
        self.numOuter, index = parseInt32(bytes, index)

        self.blocks = [[StimCon() for ki in range(self.blockLength)] for kb in range(self.numBlocks)]
        for kb in range(self.numBlocks):
            for ki in range(self.blockLength):
                index = self.blocks[kb][ki].fromBytes(bytes, index)

        for k in range(self.numInner):
            dummy, index = parseInt32(bytes, index)
        for k in range(self.numOuter):
            dummy, index = parseInt32(bytes, index)

        return index

class AxisProperties:
    label = ''
    minValue = float("NaN")
    maxValue = float("NaN")
    stepValue = float("NaN")
    showGrid = False
    def fromBytes(self, bytes, index):
        self.label, index = parseString(bytes, index)
        self.minValue, index = parseFloat32(bytes, index)
        self.maxValue, index = parseFloat32(bytes, index)
        self.stepValue, index = parseFloat32(bytes, index)
        self.showGrid, index = parseBoolean(bytes, index)
        return index
    
class GraphProperties:
    name = ''
    titleFontColor = -1
    brushColor = -1
    axisColor = -1
    showFrame = False
    showBox = False
    axisFontName = ''
    axisFontSize = -1
    xaxis = AxisProperties()
    yaxis = AxisProperties()
    def fromBytes(self, bytes, index):
        self.name, index = parseString(bytes, index)
        self.titleFontColor, index = parseInt32(bytes, index)
        self.brushColor, index = parseInt32(bytes, index)
        self.axisColor, index = parseInt32(bytes, index)
        self.showFrame, index = parseBoolean(bytes, index)
        self.showBox, index = parseBoolean(bytes, index)
        self.axisFontName, index = parseString(bytes, index)
        self.axisFontSize, index = parseInt32(bytes, index)
        index = self.xaxis.fromBytes(bytes, index)
        index = self.yaxis.fromBytes(bytes, index)
        return index
        
class AnalysisWindow:
    name = ''
    position = None
    param = None
    graph = GraphProperties()
    def fromBytes(self, bytes, index):
        self.name, index = parseString(bytes, index)
        pos = []
        for k in range(4):
           v, index = parseInt32(bytes, index) 
           pos.append(v)
        self.position = array(pos)
        self.param, index = parseKParam(bytes, index)
        index = self.graph.fromBytes(bytes, index)
        return index
        
class WaveformData:
    time_s = []
    data_uV = []
    
class ANECS(object):
    info = Info()
    equip = Equip()
    stim = Stim()
    inner = Sequence()
    outer = Sequence()
    scl = StimConList()
    resp = Resp()
    analysis = []
    waveforms = []

    def __init__(self, fname):
        self.readFile(fname)
        
    def readFile(self, fname):
        with open(fname, 'rb') as fp:
            data = fp.read()
            
            index = parseIndicator(data, 0, 'This is an ANECS data file!')
            index = self.info.fromBytes(data, index)
            index = self.equip.fromBytes(data, index)
            index = self.stim.fromBytes(data, index, self.equip.numStimChan)
            index = self.inner.fromBytes(data, index, self.info.revision)
            index = self.outer.fromBytes(data, index, self.info.revision)
            index = self.scl.fromBytes(data, index)
            index = self.resp.fromBytes(data, index)

            index = parseIndicator(data, index, 'Analysis Window')
            n, index = parseInt32(data, index)
            self.analysis = [AnalysisWindow() for k in range(n)]
            for k in range(n):
                index = self.analysis[k].fromBytes(data, index)

            ylen = -1
            
            if self.resp.saveAvgWaveform == True:
                print(f'ANECS revision: {self.info.revision}')
                self.waveforms = WaveformData()
                for k in range(self.scl.numInner):
                    fn = fname.replace('.anx', '.ch0avg0-' + str(k) + '.anx')
                    
                    if os.path.isfile(fn):                   
                        data = Path(fn).read_bytes()
                        n, index = parseInt32(data, 0)
                        y = np.frombuffer(data[4:], dtype=np.float32, count=n)
                        
                        y = y - np.mean(y[-100:])
                        y *= 1e6
                        
                        if self.info.revision < 50:
                            y /= self.resp.channels[0].gain
                                            
                        if k == 0:
                            self.waveforms.data_uV = np.zeros(shape=(self.scl.numInner, len(y)))
                            self.waveforms.data_uV[:] = np.nan
                            self.waveforms.time_s = np.arange(len(y)) * 1e-3 / self.resp.samplingRate;
                            ylen = len(y)
        
                        if len(y) == ylen:                         
                            self.waveforms.data_uV[k, :] = y
                    
                        
def parseBoolean(bytes, index):
    value = bytes[index] > 0
    index += 1
    return value, index

def parseInt32(bytes, index):
    value = int.from_bytes(bytes[slice(index, index+4)], 'little')
    index += 4
    return value, index
    
def parseFloat32(bytes, index):
    value = struct.unpack('f', bytes[slice(index, index+4)])[0]
    index += 4
    return value, index
    
                    
def parseString(bytes, index):
    n, index = parseInt32(bytes, index)
    value = bytes[slice(index, index+n)].decode('utf-8')
    index += n
    return value, index

def parseIndicator(bytes, index, requiredValue):
    value, index = parseString(bytes, index)
    
    if value != requiredValue:
        raise Exception('Error reading ANECS data file')
    
    return index


def parseKParam(bytes, index):
    n, index = parseInt32(bytes, index)
    p = []
    if n > 0:
        for k in range(0, n):
            p.append(KParam())
            index = p[k].fromBytes(bytes, index)
            
    return p, index
    

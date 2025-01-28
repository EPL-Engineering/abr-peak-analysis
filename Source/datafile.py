#!/usr/bin/env python

from __future__ import with_statement

import re, os
import numpy
from anecs_read import ANECS
from numpy import array
from datatype import abrwaveform
from datatype import abrseries
from datatype import ABRDataType
from datatype import ABRStimPolarity

def get_expt_id(fname):
    folder, fn = os.path.split(fname)
    p_id = re.compile('([\w]+-[\d]+)-')
    result = p_id.search(fn)
    id = ''
    if not result is None:
        id = result.group(1)
    return id

def get_stim_freq(fname):
    p_freq = re.compile('FREQ: ([\w.]+)')
    p_wav = re.compile('FREQ: ([\s\w.:\\\\]+).wav')
    try:
        freq = 0
        with open(fname) as f:
            data = f.read()

            header, data = data.split('DATA')
            result = p_freq.search(header)
            if not result is None:
                freqStr = result.group(1)
                if freqStr in ('clicks', 'chirp', 'noise'):
                    freq = 0
                elif p_wav.search(header) != None:
                    freq = 0
                else:
                    freq = float(freqStr)
                    
        return freq
            
    except (AttributeError, ValueError):
        return 0

def loadabr(fname, invert=False, filter=False, fdict=None, polarity=ABRStimPolarity.Avg, noiseFloor=False):
    f, ext = os.path.splitext(fname)
    if ext == '.csv':
        return loadclinicalabr(fname, invert, filter, fdict)
    if ext.lower() == '.txt':
        return loadtextfile(fname, invert, filter, fdict)
    if ext == '.anx':
        return load_anecs_file(fname, invert, filter, fdict)
    
    p_level = re.compile(':LEVELS:([\-0-9.; Inf]+)')
    p_fs = re.compile('SAMPLE \(.sec\): ([0-9.]+)')
    p_freq = re.compile('FREQ: ([\w.]+)')
    p_wav = re.compile('FREQ: ([\s\w.:\\\\]+).wav')
    p_varywhich = re.compile(':Vary signal level: (?i)(true|false)')
    p_control = re.compile(':Control:([\-0-9; Inf NaN]+)')
    time_pattern = '([\d]{1,2}/[\d]{1,2}/[\d]{4}[\t\s]' + \
                  '[\d]{1,2}:[\d]{1,2}(:[\d]{1,2})?\s[APM]{2})'
    p_time = re.compile(time_pattern)
    
    abr_window = 8500 #usec

    dataType = ABRDataType.CFTS

    folder,fn=os.path.split(fname)
    isVsEP = fn.startswith('VsEP')
    if isVsEP:
        dataType = ABRDataType.VsEP
    
    try:
        with open(fname, encoding='latin-1') as f:
            data = f.read()
            
            if data.startswith('[STANDARD ABR]'):
                return load_comprehensive_cfts_data(fname, invert, filter, fdict)

            if data.startswith('[FAST ABR]'):
                return load_fast_abr_data(fname, invert, filter, fdict)

            header, data = data.split('DATA')

            levelstring = p_level.search(header).group(1).strip(';').split(';')
            if levelstring[0] == " ":
                levels = array([0], dtype='f')
            else:
                levels = array(levelstring).astype(float)

            sampling_period = float(p_fs.search(header).group(1))
            fs = 1e6/sampling_period
            cutoff = abr_window / sampling_period

            controlStr = p_control.search(header)
            if controlStr == None:
                controlVal = float('-inf')
            else:
                controlVal = float(controlStr.group(1))
                
            varyWhich = p_varywhich.search(header)
            if varyWhich == None:
                varyMasker = numpy.any(levels == controlVal)
            else:
                varyMasker = varyWhich.group(1).lower() == 'false'

            data = array(data.split()).astype(float)

            cutoff = int(len(data)/len(levels) / 2);
            data = data.reshape(int(len(data) / len(levels)), len(levels)).T
            
            dataSum = data[:,:cutoff]
            dataDiff = data[:, cutoff:]
            
            # compute condensation and rarefaction traces from sum and difference
            dataCond = dataSum + dataDiff
            dataRare = dataSum - dataDiff            

            # select the stimulus polarity specified by the user
            if polarity == ABRStimPolarity.Avg:
                data = dataSum;
            if polarity == ABRStimPolarity.Condensation:
                data = dataCond
            if polarity == ABRStimPolarity.Rarefaction:
                data = dataRare
            
            if invert:
                data = -data

            waveforms = [abrwaveform(fs, w, l) for w, l in zip(data, levels)]

            # Checks for an ABR I-O bug that sometimes saves zeroed waveforms
            # Also excludes controls
            for w in waveforms[:]:
                if (w.y==0).all() or w.level==controlVal:
                    waveforms.remove(w)

            if filter:
                waveforms = [w.filtered(**fdict) for w in waveforms]
            
            # parse stimulus waveform description
            if isVsEP:
                freq = -1
            else:
                result = p_freq.search(header)
                if result is None:
                    freq = 0
                else:
                    freqStr = p_freq.search(header).group(1)
                    if freqStr in ('clicks', 'chirp', 'noise'):
                        freq = 0
                    elif p_wav.search(header) != None:
                        freq = 0
                    else:
                        freq = float(freqStr)

            # Instantiate ABR series                    
            series = abrseries(waveforms, freq, None, dataType, polarity, varyMasker)
            series.compute_corrcoefs()
            series.filename = fname
            series.time = p_time.search(header).group(1)
            series.Tmax = cutoff / fs * 1000

            if noiseFloor:
                series.find_noise_floor(dataDiff)

            return series

    except (AttributeError, ValueError):
        msg = 'Could not parse %s.  Most likely not a valid ABR file.' % fname
        raise IOError(msg)


def load_comprehensive_cfts_data(fname, invert=False, filter=False, fdict=None, polarity=ABRStimPolarity.Avg, noiseFloor=False):

    p_level = re.compile('Levels=([\-0-9.; Inf]+)')
    p_fs = re.compile('Response.Sampling rate \(Hz\)=([0-9.]+)')
    p_win = re.compile('Response.Window \(ms\)=([0-9.]+)')
    p_freq = re.compile('Stimulus.Frequency \(kHz\)=([0-9.]+)')
    p_wav = re.compile('Stimulus.Waveform=([\s\w]+)\n')
    p_time = re.compile('Date=([\w\d/\s:]+)\n')

    try:
        with open(fname, encoding='latin-1') as f:
            data = f.read()
            
            header, data = data.split('[DATA]')

            levelstring = p_level.search(header).group(1).strip(';').split(';')
            if levelstring[0] == " ":
                levels = array([0], dtype='f')
            else:
                levels = array(levelstring).astype(float)

            fs = float(p_fs.search(header).group(1))
            abr_window = float(p_win.search(header).group(1))

            data = data.split('\n', 2)
            data = array(data[2].split()).astype(float)

            ncol = len(levels) * 2 + 1
            data = data.reshape(int(len(data) / ncol), ncol).T
            
            dataSum = data[1:len(levels)+1,:]
            dataDiff = data[(len(levels) + 1):, :]
            
            # compute condensation and rarefaction traces from sum and difference
            dataCond = dataSum + dataDiff
            dataRare = dataSum - dataDiff            

            # select the stimulus polarity specified by the user
            if polarity == ABRStimPolarity.Avg:
                data = dataSum;
            if polarity == ABRStimPolarity.Condensation:
                data = dataCond
            if polarity == ABRStimPolarity.Rarefaction:
                data = dataRare
            
            if invert:
                data = -data

            waveforms = [abrwaveform(fs, w, l) for w, l in zip(data, levels)]

            # Checks for an ABR I-O bug that sometimes saves zeroed waveforms
            # Also excludes controls
            for w in waveforms[:]:
                if (w.y==0).all():
                    waveforms.remove(w)

            if filter:
                waveforms = [w.filtered(**fdict) for w in waveforms]
            
            waveShape = p_wav.search(header).group(1)
            
            if waveShape == 'CLICK':
                freq = 0
            else:
                freq = float(p_freq.search(header).group(1))


            dataType = ABRDataType.CFTS
            varyMasker = False
            
            # Instantiate ABR series                    
            series = abrseries(waveforms, freq, None, dataType, polarity, varyMasker)
            series.compute_corrcoefs()
            series.filename = fname
            series.time = p_time.search(header).group(1)
            series.Tmax = abr_window

            if noiseFloor:
                series.find_noise_floor(dataDiff)

            return series

    except (AttributeError, ValueError):
        msg = 'Could not parse %s.  Most likely not a valid ABR file.' % fname
        raise IOError(msg)
                                 

def load_fast_abr_data(fname, invert=False, filter=False, fdict=None, polarity=ABRStimPolarity.Avg, noiseFloor=False):

    p_level = re.compile('Levels=([\-0-9.; Inf]+)')
    p_fs = re.compile('Response.Fs \(Hz\)=([0-9.]+)')
    p_win = re.compile('Response.Window \(ms\)=([0-9.]+)')
    p_freq = re.compile('Frequency \(kHz\)=([0-9.]+)')
    p_time = re.compile('Date=([\w\d/\s:]+)\n')

    try:
        with open(fname, encoding='latin-1') as f:
            data = f.read()
            
            header, data = data.split('[DATA]')

            levelstring = p_level.search(header).group(1).strip(';').split(';')
            if levelstring[0] == " ":
                levels = array([0], dtype='f')
            else:
                levels = array(levelstring).astype(float)

            fs = float(p_fs.search(header).group(1))
            abr_window = float(p_win.search(header).group(1))

            data = data.split('\n', 2)
            data = array(data[2].split()).astype(float)

            ncol = len(levels) * 2 + 1
            data = data.reshape(int(len(data) / ncol), ncol).T
            
            dataSum = data[1:len(levels)+1,:]
            dataDiff = data[(len(levels) + 1):, :]
            
            # compute condensation and rarefaction traces from sum and difference
            dataCond = dataSum + dataDiff
            dataRare = dataSum - dataDiff            

            # select the stimulus polarity specified by the user
            if polarity == ABRStimPolarity.Avg:
                data = dataSum;
            if polarity == ABRStimPolarity.Condensation:
                data = dataCond
            if polarity == ABRStimPolarity.Rarefaction:
                data = dataRare
            
            if invert:
                data = -data

            waveforms = [abrwaveform(fs, w, l) for w, l in zip(data, levels)]

            # Checks for an ABR I-O bug that sometimes saves zeroed waveforms
            # Also excludes controls
            for w in waveforms[:]:
                if (w.y==0).all():
                    waveforms.remove(w)

            if filter:
                waveforms = [w.filtered(**fdict) for w in waveforms]
            
            freq = float(p_freq.search(header).group(1))


            dataType = ABRDataType.CFTS
            varyMasker = False
            
            # Instantiate ABR series                    
            series = abrseries(waveforms, freq, None, dataType, polarity, varyMasker)
            series.compute_corrcoefs()
            series.filename = fname
            series.time = p_time.search(header).group(1)
            series.Tmax = abr_window

            if noiseFloor:
                series.find_noise_floor(dataDiff)

            return series

    except (AttributeError, ValueError):
        msg = 'Could not parse %s.  Most likely not a valid ABR file.' % fname
        raise IOError(msg)
                                 

def loadclinicalabr(fname, invert=False, filter=False, fdict=None):

    try:
        with open(fname) as f:
            data = f.read()
            header, data = data.split('\n', 1)

            numCols = len(header.split(','))

#            levels = array('-1').astype(float)
            levels = [0, 1, 2]

            data = array(data.replace(',', ' ').split()).astype(float)
            data = data.reshape(len(data)/numCols, numCols).T

            t = data[0,:]
            if numCols > 4:
                data = data[3:5, :]
            else:
                data = data[1:, :]

            data = 1e6 * data            
            
            sampling_period = t[1] - t[0]
            fs = 1/sampling_period

            if invert:
                data = -data

#            waveforms = [abrwaveform(fs, data(1,:), 0), abrwaveform(fs, data(2,:), 1), abrwaveform(fs, data(3,:), 2)]
            waveforms = [abrwaveform(fs, w, l) for w, l in zip(data, levels)]

            #Checks for a ABR I-O bug that sometimes saves zeroed waveforms
            for w in waveforms[:]:
                if (w.y==0).all():
                    waveforms.remove(w)

            if filter:
                waveforms = [w.filtered(**fdict) for w in waveforms]

            freq = -1
            series = abrseries(waveforms, freq, None, ABRDataType.Clinical, ABRStimPolarity.Avg)
            abrseries.filename = fname
            abrseries.time = t
            abrseries.Tmax = max(t) * 1000
            return series

    except (AttributeError, ValueError):
        msg = 'Could not parse %s.  Most likely not a valid CSV file.' % fname
        raise IOError(msg)
    
def loadtextfile(fname, invert=False, filter=False, fdict=None):

#    p_level = re.compile(':LEVELS:([\-0-9;]+)')
#    p_fs = re.compile('SAMPLE \(.sec\): ([0-9]+)')
#    p_freq = re.compile('FREQ: ([\w.]+)')
    
    try:
        with open(fname) as f:
            data = f.read()
            
            if data.startswith('Identifier:'):
                return load_caspary_text_file(fname, invert, filter, fdict)
                            
            header, data = data.split('\n', 1)

            cols = header.split('\t')
            numCols = len(cols)

#            levelString = re.findall('kHz([0-9]+)dB', header)
            levelString = re.findall('([0-9]+)[\s]+dBSPL', header)
            levels = array(levelString).astype(float)

            data = array(data.replace(',', ' ').split()).astype(float)
            nrows = (int)(len(data)/numCols)
            data = data.reshape(nrows, numCols).T

            t = data[0,:]
            data = 1e6 * data[1:, :]
            
            sampling_period = t[1] - t[0]
            fs = 1/sampling_period

            if invert:
                data = -data

            waveforms = [abrwaveform(fs, w, l) for w, l in zip(data, levels)]

            if filter:
                waveforms = [w.filtered(**fdict) for w in waveforms]

            #freq = float(re.search('([0-9]+)kHz', header).group(1))
            freq = 0
            series = abrseries(waveforms, freq, None, ABRDataType.CFTS, ABRStimPolarity.Avg)
            series.compute_corrcoefs()
            abrseries.filename = fname

            #Temporary -- add code to convert to actual date/time object
            abrseries.time = t
            abrseries.Tmax = max(t) * 1000
            return series

    except (AttributeError, ValueError):
        msg = 'Could not parse %s.  Most likely not a valid CSV file.' % fname
        raise IOError(msg)
    
def load_caspary_text_file(fname, invert=False, filter=False, fdict=None):

    try:
        with open(fname) as f:
            data = f.read()
            
            levelStr = re.compile('Intensity:([\d,]+)').search(data).group(1)
            levelList = re.compile(',+([\d]+)').findall(levelStr)
            levels = [float(x) for x in levelList]
            
            dtStr = re.compile('Smp. Period:([\d\.,]+)').search(data).group(1)
            dtList = re.compile(',+([\d\.]+)').findall(dtStr)
            dt = [float(x) for x in dtList]
            
            freqStr = re.compile('Stim. Freq.([\d,]+)').search(data).group(1)
            freqList = re.compile(',+([\d]+)').findall(freqStr)
            freqs = [float(x) for x in freqList]

            zeroStr = re.compile('Zero Position:([\d,]+)').search(data).group(1)
            zeroList = re.compile(',+([\d]+)').findall(zeroStr)
            zeroPositions = [float(x) for x in zeroList]
            izero = int(zeroPositions[0])
            
            dataStr = data.split('Data Pnt')[1].split('\n', 1)[1]
            a = array(dataStr.replace(',', ' ').split()).astype(float)
            numCols = len(levels) * 6 + 1
            y = a.reshape(int(len(a) / numCols), numCols).T

            t = (y[0,:] - y[0,0]) * dt[0] * 1e-6
            t0 = t[izero]

            istart = (abs(y[1,:])!=0).argmax()
            istart = izero
            y = y[:, istart:]
            t = t[istart:] - t0

            data = y[2::6, :]
            
            fs = 1e6 / dt[0]

            if invert:
                data = -data

            waveforms = [abrwaveform(fs, w, l) for w, l in zip(data, levels)]

            if filter:
                waveforms = [w.filtered(**fdict) for w in waveforms]

            series = abrseries(waveforms, freqs[0] / 1000, None, ABRDataType.CFTS, ABRStimPolarity.Avg)
            series.compute_corrcoefs()
            abrseries.filename = fname

            #Temporary -- add code to convert to actual date/time object
            abrseries.time = t
            abrseries.Tmax = max(t) * 1000
            return series
            
    except (AttributeError, ValueError):
        msg = 'Could not parse %s.  Most likely not a valid CSV file.' % fname
        raise IOError(msg)
            
def load_anecs_file(fname, invert=False, filter=False, fdict=None):

    try:
        anecs = ANECS(fname)
        levels = anecs.inner.vals
        
        ichan = int(anecs.inner.channels)
        freq = anecs.stim.channels[ichan-1].param[0].value
        
        fs = anecs.resp.samplingRate * 1000
        t = anecs.waveforms.time_s
        data = anecs.waveforms.data_uV

        if invert:
            data = -data

        waveforms = [abrwaveform(fs, w, l) for w, l in zip(data, levels)]

        if filter:
            waveforms = [w.filtered(**fdict) for w in waveforms]

        series = abrseries(waveforms, freq, None, ABRDataType.CFTS, ABRStimPolarity.Avg)
        series.compute_corrcoefs()
        abrseries.filename = fname

        #Temporary -- add code to convert to actual date/time object
        abrseries.time = t
        abrseries.Tmax = max(t) * 1000
        return series
            
    except (AttributeError, ValueError):
        msg = 'Could not parse %s.  Most likely not a valid ANECS data file.' % fname
        raise IOError(msg)
            

## Changelog

### v1.11 (unreleased)
#### Added
- support for Fast ABR data files

---

### v1.10.1 (2025-01-10)
#### Fixed 
- fixed bug using **X** key to clear previous work
- fixed formatting bug writing threshold to analysis file

---

### v1.10 (2024-10-24)
#### Fixed
- fixed bug where it was not possible to invert and normalize the waveforms
#### Added
- support for CFTS data files with comprehensive headers

---

### v1.9.0 (2023-08-06)  
#### Added
- checkbox on Options gui to automatically restore previous analysis when loading data (default = True)
- clear analysis using **X** key (restarts from default peak guess)
- File menu options to clear all tabs and clear all but selected tabs
- use of numeric keypad +/- keys to scale waveforms
 
---

### v1.8.0 (2023-07-26) 
#### Added
- option to restore previous analysis, using **R** key 

---

### Older
Summary of pre-GitHub changes

| Version | Date | Description |
| --- | --- | --- |
| 1.7.1.71 | 2023-02-09 | ANECS average waveforms after rev50 have the gain applied. Modified code to take that into account |
| 1.7.0.70 | 2023-01-26 | Added noise floor option. |
| 1.6.1.69 | 2022-12-16 | Account for zero position in IHS data |
| 1.6.0.67 | 2022-12-09 | -made extension check case-insensitive<br>-added .anx and .txt filters to open file dialog<br>-fixed option to load multiple files through the dialog<br>-explicitly scale x-axis of work plot |
| 1.6.0.65 | 2022-12-07 | - updated to Anaconda Python 3.9<br>- added code to read ANECS data |
| 1.5.8.62 | 2021-08-21 | - added file extension option<br>- added export filtered waveforms option<br>- crashed in Windows, if saved startdir didn't exist. Config file path not created correctly (missing file separator) |
| 1.5.7.61 | 2021-01-21 | fixed bug exporting data with only one trace |
| 1.5.7.60 | 2019-11-12 | rehabilitated text file read |
| 1.5.6.58 | 2019-09-26 | updated help documents |
| 1.5.5.56 | 2019-09-25 | - added P key to toggle waveform polarity<br>-cleaned up keybindings help page |
| 1.5.4.54 | 2019-05-05 | - power2 fit modified to handle negative levels (e.g. when level is in dB re 1V)<br>-suppressed audiogram minor tick labels. |
| 1.5.3.52 | 2019-04-26 | - applied Kirupa's tweaks to her algorithm<br>- added case to get correct preferences location on PC |
| 1.5.0.47 | 2019-02-01 | added auto threshold summary to output files |
| 1.5.0.42 | 2019-01-31 | updated to Python 3.7 |
| 1.3.0.32 | 2018-04-04 | - added audiogram capability<br>- added automatic thresholding using Kirupa's algorithm |
| 1.2.0.13 | 2017-01-13 | added "noise" to list of waveforms |
| 1.2.0.11 | 2016-09-29 | - autoscale time-axis<br>- added function to read .txt data files |
| 1.0.0.10 | 2015-11-13 | reads in data with wav file name in FREQ: field |
| 1.1.1.9 | 2015-03-05 | - handle 'chirp' and 'clicks' frequency specifications without error<br>- added control for window over which to compute the baseline statistics<br>- added option to specify min latency<br>- added ability to analyze each stimulus polarity separately<br>- added ability to read CSV data exported from clinical ABR software |
| 0.9.0.2 | 2013-09-04 |  read VsEP data files without error |













:: C:\ProgramData\miniforge3\condabin\activate.bat
:: C:\Users\kehan\miniforge3\condabin\activate.bat
:: conda activate abr
pyinstaller --noconfirm notebook.spec
"D:\Development\3rd Party\verpatch\verpatch.exe" .\dist\notebook\notebook.exe 1.11.0.0 /va
"C:\Program Files (x86)\Inno Setup 6\Compil32.exe" /cc "D:\Development\abr-peak-analysis\Installer\ABR_Peak_Analysis_Installer.iss"

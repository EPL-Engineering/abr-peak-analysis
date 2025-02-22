; -- ABR_Peak_Analysis_Installer.iss --

; Set the following three variables
#define buildPath "..\Source\dist\notebook\"
#define exeName "notebook.exe" ; i.e.: the "Target filename" set in the LabVIEW project explorer
#define appName "ABR Peak Analysis"    ; this is arbitrary. It controls the install folder location and the desktop shortcut name
#define iconName "icon.ico"

; In normal use, should not need to edit below here

; Extracts the semantic version from the executable. Only retains the patch number if it is greater than zero.
#define SemanticVersion() \
   GetVersionComponents(buildPath + exeName, Local[0], Local[1], Local[2], Local[3]), \
   Str(Local[0]) + "." + Str(Local[1]) + ((Local[2]>0) ? "." + Str(Local[2]) : "")
    
; The installer contains the semantic version number, but replaces the dots with dashes so it doesn't look like a file extension.
#define installerName StringChange(appName, ' ', '_') + "_" + StringChange(SemanticVersion(), '.', '-')

[Setup]
AppName={#appName}
AppVerName={#appName} V{#SemanticVersion}
DefaultDirName={pf}\EPL\{#appName}
OutputDir=D:\Development\abr-peak-analysis\Installer\Output
DefaultGroupName=EPL
AllowNoIcons=yes
OutputBaseFilename={#installerName}
UsePreviousAppDir=no
UsePreviousGroup=no
DisableProgramGroupPage=yes
PrivilegesRequired=admin

[Files]
Source: "..\Source\dist\notebook\*.*"; DestDir: "{app}"; Excludes: "*.dll.c~,\mpl-data\fonts,\mpl-data\sample_data"; Flags: replacesameversion
Source: "..\Source\dist\notebook\_internal\*.*"; DestDir: "{app}\_internal"; Excludes: "*.dll.c~,\mpl-data\fonts,\mpl-data\sample_data"; Flags: replacesameversion recursesubdirs

[Icons]
Name: "{commondesktop}\{#appName}"; Filename: "{app}\notebook.exe"; IconFilename: "{app}\_internal\{#iconName}"; IconIndex: 0

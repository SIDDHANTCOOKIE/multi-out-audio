; Inno Setup script. Build: ISCC /DAppVersion=1.1.0 installer\multiout.iss  (expects dist\MultiOutAudio.exe)
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F1E2C9A-7B1D-4E6B-9A55-3D2B8C0A41F7}
AppName=Multi-Out Audio
AppVersion={#AppVersion}
AppPublisher=SIDDHANTCOOKIE
AppPublisherURL=https://github.com/SIDDHANTCOOKIE/multi-out-audio
AppSupportURL=https://github.com/SIDDHANTCOOKIE/multi-out-audio/issues
DefaultDirName={autopf}\Multi-Out Audio
DefaultGroupName=Multi-Out Audio
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=MultiOutAudio-Setup-{#AppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\MultiOutAudio.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startup"; Description: "Start Multi-Out Audio when I sign in"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\MultiOutAudio.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Multi-Out Audio"; Filename: "{app}\MultiOutAudio.exe"
Name: "{autodesktop}\Multi-Out Audio"; Filename: "{app}\MultiOutAudio.exe"; Tasks: desktopicon
Name: "{userstartup}\Multi-Out Audio"; Filename: "{app}\MultiOutAudio.exe"; Tasks: startup

[Run]
Filename: "{app}\MultiOutAudio.exe"; Description: "Launch Multi-Out Audio"; Flags: nowait postinstall skipifsilent

[Setup]
AppName=SentinelAI
AppVersion=1.0
AppPublisher=Mojeed Olaleke Salako
AppPublisherURL=https://www.roehampton.ac.uk
DefaultDirName={autopf}\SentinelAI
DefaultGroupName=SentinelAI
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=SentinelAI_Setup
SetupIconFile=assets\Logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64os

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SentinelAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\Logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\exports"

[Icons]
Name: "{group}\SentinelAI"; Filename: "{app}\SentinelAI.exe"; IconFilename: "{app}\Logo.ico"
Name: "{group}\{cm:UninstallProgram,SentinelAI}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SentinelAI"; Filename: "{app}\SentinelAI.exe"; IconFilename: "{app}\Logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\SentinelAI.exe"; Description: "{cm:LaunchProgram,SentinelAI}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\exports"

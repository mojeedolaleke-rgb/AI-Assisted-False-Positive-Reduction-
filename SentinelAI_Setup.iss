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
Source: "python-3.10.11-amd64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Dirs]
Name: "{app}\exports"

[Icons]
Name: "{group}\SentinelAI"; Filename: "{app}\SentinelAI.exe"; IconFilename: "{app}\Logo.ico"
Name: "{group}\{cm:UninstallProgram,SentinelAI}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SentinelAI"; Filename: "{app}\SentinelAI.exe"; IconFilename: "{app}\Logo.ico"; Tasks: desktopicon

[Code]
function IsPythonInstalled(): Boolean;
var
  PythonPath: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.9\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.9\InstallPath', '', PythonPath);
end;

procedure InstallDependencies();
var
  PythonExe: String;
  ResultCode: Integer;
begin
  if not IsPythonInstalled() then
  begin
    WizardForm.StatusLabel.Caption := 'Installing Python 3.10...';
    Exec(ExpandConstant('{tmp}\python-3.10.11-amd64.exe'),
      '/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1',
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;

  if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonExe) or
     RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonExe) then
    PythonExe := PythonExe + 'python.exe'
  else
    PythonExe := 'python.exe';

  WizardForm.StatusLabel.Caption := 'Installing security scanning tools...';
  Exec(PythonExe, '-m pip install semgrep --quiet --no-warn-script-location',
    '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    InstallDependencies();
end;

[Run]
Filename: "{app}\SentinelAI.exe"; Description: "{cm:LaunchProgram,SentinelAI}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\exports"

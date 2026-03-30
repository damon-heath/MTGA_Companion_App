[ISPP]
#define RepoRoot AddBackslash(SourcePath) + "..\\..\\"

[Setup]
AppId={{A2D8A3E9-2F17-4E94-A6B7-4A3DE80C8E5A}
AppName=Arena Companion
AppVersion=1.1.0
PrivilegesRequired=lowest
DefaultDirName={autopf}\Arena Companion
DefaultGroupName=Arena Companion
OutputDir={#RepoRoot}build\installer\dist
OutputBaseFilename=ArenaCompanionSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "{#RepoRoot}dist\ArenaCompanion\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Arena Companion"; Filename: "{app}\ArenaCompanion.exe"
Name: "{autodesktop}\Arena Companion"; Filename: "{app}\ArenaCompanion.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:";

[Run]
Filename: "{app}\ArenaCompanion.exe"; Description: "Launch Arena Companion"; Flags: nowait postinstall skipifsilent

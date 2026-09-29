; ============================================================
;  Refat's Android Full Backup V1.0.1 — Inno Setup Installer Script
;  Developer : Robiul Islam Refat
;  Website   : www.refatishere.free.nf
;  Contact   : rbl.islam.refat2@gmail.com
;  GitHub    : https://github.com/refatwashere/AndroidBackup
; ============================================================

#define AppName      "Refat's Android Full Backup"
#define AppVersion   "1.0.1"
#define AppPublisher "Robiul Islam Refat"
#define AppURL       "https://github.com/refatwashere/AndroidBackup"
#define AppWebsite   "www.refatishere.free.nf"
#define AppContact   "rbl.islam.refat2@gmail.com"
#define AppExeName   "RefatAndroidBackup.exe"
#define AppID        "{{B2C3D4E5-F6A7-8901-BCDE-F12345678901}"

[Setup]
AppId={#AppID}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} V{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
AppContact={#AppContact}
AppCopyright=Copyright (C) 2026 {#AppPublisher}
DefaultDirName={autopf}\RefatAndroidBackup
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=EULA.txt
InfoBeforeFile=WELCOME.txt
InfoAfterFile=FINISH.txt
OutputDir=installer_output
OutputBaseFilename=RefatAndroidBackup_V{#AppVersion}_Setup
SetupIconFile=assets\Icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
WizardImageFile=assets\wizard_sidebar.bmp
WizardSmallImageFile=assets\wizard_small.bmp
DisableProgramGroupPage=no
DisableWelcomePage=no
ShowLanguageDialog=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} V{#AppVersion}
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Installer
VersionInfoCopyright=Copyright (C) 2026 {#AppPublisher}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}.0
MinVersion=6.1sp1
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";  Description: "Create a &desktop shortcut";              GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "quicklaunch";  Description: "Create a &Quick Launch shortcut";         GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startupicon";  Description: "Launch automatically at &Windows startup"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Main executable
Source: "dist\RefatAndroidBackup\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Python DLL (must be next to exe)
Source: "dist\RefatAndroidBackup\python314.dll"; DestDir: "{app}"; Flags: ignoreversion

; All _internal files (recursive)
Source: "dist\RefatAndroidBackup\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; License and docs
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "EULA.txt";    DestDir: "{app}"; Flags: ignoreversion
Source: "README.md";   DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";                       Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\README";                           Filename: "{app}\README.md"
Name: "{group}\License";                          Filename: "{app}\LICENSE.txt"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}";                 Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunch
Name: "{userstartup}\{#AppName}";                 Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Registry]
Root: HKCU; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}";          Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "Version";     ValueData: "{#AppVersion}"
Root: HKCU; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "Website";     ValueData: "{#AppWebsite}"
Root: HKCU; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "Contact";     ValueData: "{#AppContact}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM {#AppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}"

[Code]
var
  DevInfoLabel: TNewStaticText;

procedure InitializeWizard();
begin
  DevInfoLabel := TNewStaticText.Create(WizardForm);
  DevInfoLabel.Parent := WizardForm.WelcomePage;
  DevInfoLabel.Left   := WizardForm.WelcomeLabel2.Left;
  DevInfoLabel.Top    := WizardForm.WelcomeLabel2.Top + WizardForm.WelcomeLabel2.Height + 16;
  DevInfoLabel.Width  := WizardForm.WelcomeLabel2.Width;
  DevInfoLabel.AutoSize := False;
  DevInfoLabel.Height := 80;
  DevInfoLabel.Caption :=
    'Developer : Robiul Islam Refat' + #13#10 +
    'Website   : www.refatishere.free.nf' + #13#10 +
    'Contact   : rbl.islam.refat2@gmail.com' + #13#10 +
    'GitHub    : github.com/refatwashere/AndroidBackup';
  DevInfoLabel.Font.Color := $00888888;
  DevInfoLabel.Font.Size  := 8;
end;

function InitializeUninstall(): Boolean;
begin
  Result := MsgBox(
    'Are you sure you want to completely remove Refat''s Android Full Backup and all of its components?',
    mbConfirmation, MB_YESNO) = IDYES;
end;

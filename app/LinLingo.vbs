' LinLingo launcher - starts the app with no console window at all.
' If double-clicking this file does nothing, run the diagnose batch file,
' or just use run.bat (it shows a console, but always works).
Option Explicit
On Error Resume Next

Dim sh, fso, baseDir, target
Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

If Err.Number <> 0 Then
    MsgBox "Cannot create WScript.Shell. Windows Script Host may be disabled.", 16, "LinLingo"
    WScript.Quit 1
End If

baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = baseDir

target = baseDir & "\run.bat"
If Not fso.FileExists(target) Then
    MsgBox "run.bat not found: " & target, 16, "LinLingo"
    WScript.Quit 1
End If

' window style 0 = hidden, so no console window appears
sh.Run "cmd /c """ & target & """", 0, False

If Err.Number <> 0 Then
    MsgBox "Launch failed: " & Err.Description, 16, "LinLingo"
End If

#Requires AutoHotkey v2.0
#SingleInstance Force

; Only active when a real cmd.exe has focus
#HotIf WinActive("ahk_exe cmd.exe")

^Space::  ; Ctrl+Space
{
    static isTop := false
    hwnd := WinExist("A")            ; get the active window’s handle
    if !hwnd
        return

    ; Toggle between TOPMOST (-1) and NOTOPMOST (-2)
    flag := isTop ? -2 : -1
    DllCall(
        "User32.dll\SetWindowPos"
      , "Ptr", hwnd
      , "Ptr", flag
      , "Int", 0, "Int", 0, "Int", 0, "Int", 0
      , "UInt", 0x0001|0x0002       ; SWP_NOSIZE | SWP_NOMOVE
    )
    isTop := !isTop
}

#HotIf

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\bogda\OneDrive\Desktop\gptwrapped"
WshShell.Run """C:\Users\bogda\AppData\Local\Programs\Python\Python314\pythonw.exe"" ""C:\Users\bogda\OneDrive\Desktop\gptwrapped\gui.py""", 0, False

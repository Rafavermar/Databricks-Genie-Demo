param(
    [Parameter(Mandatory = $true)]
    [string]$Url,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [int]$WaitSeconds = 15,
    [int]$ZoomOutSteps = 0,
    [switch]$Fullscreen,
    [int]$ClickX = -1,
    [int]$ClickY = -1,
    [int]$PostClickWaitSeconds = 6
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class BrowserCaptureNative
{
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern void SwitchToThisWindow(IntPtr hWnd, bool altTab);

    [DllImport("user32.dll")]
    public static extern void keybd_event(byte virtualKey, byte scanCode, uint flags, UIntPtr extraInfo);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int command);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int command);

    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(
        IntPtr hWnd,
        IntPtr hWndInsertAfter,
        int x,
        int y,
        int width,
        int height,
        uint flags
    );

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    public static extern void mouse_event(
        uint flags,
        uint dx,
        uint dy,
        uint data,
        UIntPtr extraInfo
    );
}
"@

$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = [System.IO.Path]::GetDirectoryName($resolvedOutput)
[System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null

$browser = Get-Process -Name chrome -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } |
    Select-Object -First 1

if (-not $browser) {
    Start-Process chrome.exe
    Start-Sleep -Seconds 3
    $browser = Get-Process -Name chrome -ErrorAction Stop |
        Where-Object { $_.MainWindowHandle -ne 0 } |
        Select-Object -First 1
}

if (-not $browser) {
    throw "No se pudo abrir una ventana principal de Chrome."
}

$handle = $browser.MainWindowHandle
[BrowserCaptureNative]::ShowWindow($handle, 9) | Out-Null
Start-Sleep -Milliseconds 500
[BrowserCaptureNative]::ShowWindow($handle, 3) | Out-Null
Start-Sleep -Milliseconds 500
[BrowserCaptureNative]::SetWindowPos(
    $handle,
    [IntPtr](-1),
    0,
    0,
    0,
    0,
    0x0043
) | Out-Null

$shell = New-Object -ComObject WScript.Shell
for ($attempt = 0; $attempt -lt 5; $attempt++) {
    [BrowserCaptureNative]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero)
    $shell.AppActivate($browser.Id) | Out-Null
    [BrowserCaptureNative]::SwitchToThisWindow($handle, $true)
    [BrowserCaptureNative]::SetForegroundWindow($handle) | Out-Null
    [BrowserCaptureNative]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 500
    if ([BrowserCaptureNative]::GetForegroundWindow() -eq $handle) {
        break
    }
}

if ([BrowserCaptureNative]::GetForegroundWindow() -ne $handle) {
    [BrowserCaptureNative]::SetWindowPos(
        $handle,
        [IntPtr](-2),
        0,
        0,
        0,
        0,
        0x0043
    ) | Out-Null
    throw "Chrome no pudo convertirse en la ventana activa."
}

[System.Windows.Forms.SendKeys]::SendWait("^l")
[System.Windows.Forms.SendKeys]::SendWait($Url)
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
Start-Sleep -Seconds $WaitSeconds

[System.Windows.Forms.SendKeys]::SendWait("{ESC}")
[System.Windows.Forms.SendKeys]::SendWait("{HOME}")
[System.Windows.Forms.SendKeys]::SendWait("^0")
for ($index = 0; $index -lt $ZoomOutSteps; $index++) {
    [System.Windows.Forms.SendKeys]::SendWait("^(-)")
    Start-Sleep -Milliseconds 250
}
[System.Windows.Forms.SendKeys]::SendWait("^{HOME}")
Start-Sleep -Seconds 4

if ($Fullscreen) {
    [System.Windows.Forms.SendKeys]::SendWait("{F11}")
    Start-Sleep -Seconds 5
}

try {
    if ($ClickX -ge 0 -and $ClickY -ge 0) {
        [BrowserCaptureNative]::SwitchToThisWindow($handle, $true)
        [BrowserCaptureNative]::SetForegroundWindow($handle) | Out-Null
        [BrowserCaptureNative]::SetCursorPos($ClickX, $ClickY) | Out-Null
        Start-Sleep -Seconds 1
        [BrowserCaptureNative]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 150
        [BrowserCaptureNative]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Seconds $PostClickWaitSeconds
    }

    $rect = $null
    $width = 0
    $height = 0
    for ($attempt = 0; $attempt -lt 5; $attempt++) {
        $rect = New-Object BrowserCaptureNative+RECT
        if ([BrowserCaptureNative]::GetWindowRect($handle, [ref]$rect)) {
            $width = $rect.Right - $rect.Left
            $height = $rect.Bottom - $rect.Top
            if ($width -ge 800 -and $height -ge 600 -and $rect.Left -gt -10000) {
                break
            }
        }

        [BrowserCaptureNative]::ShowWindow($handle, 9) | Out-Null
        Start-Sleep -Milliseconds 500
        [BrowserCaptureNative]::ShowWindow($handle, 3) | Out-Null
        $shell.AppActivate($browser.Id) | Out-Null
        [BrowserCaptureNative]::SetForegroundWindow($handle) | Out-Null
        Start-Sleep -Seconds 1
    }

    if ($width -lt 800 -or $height -lt 600 -or $rect.Left -le -10000) {
        throw "La ventana de Chrome no alcanzó dimensiones capturables."
    }

    $bitmap = New-Object System.Drawing.Bitmap $width, $height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CopyFromScreen(
            $rect.Left,
            $rect.Top,
            0,
            0,
            (New-Object System.Drawing.Size $width, $height)
        )
        $bitmap.Save($resolvedOutput, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}
finally {
    if ($Fullscreen) {
        [BrowserCaptureNative]::SetForegroundWindow($handle) | Out-Null
        [System.Windows.Forms.SendKeys]::SendWait("{F11}")
    }
    [BrowserCaptureNative]::SetWindowPos(
        $handle,
        [IntPtr](-2),
        0,
        0,
        0,
        0,
        0x0043
    ) | Out-Null
}

Write-Output $resolvedOutput

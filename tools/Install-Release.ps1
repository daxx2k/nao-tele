[CmdletBinding()]
param([ValidateSet('Quest')][string]$Device='Quest',
      [Parameter(Mandatory=$true)][string]$Serial,
      [string]$Adb='adb')
$ErrorActionPreference='Stop'
$apk=Join-Path $PSScriptRoot "TeleNao-$Device.apk"
if(-not (Test-Path -LiteralPath $apk)){$apk=Join-Path (Split-Path $PSScriptRoot -Parent) "dist\TeleNao-$Device.apk"}
if(-not (Test-Path -LiteralPath $apk)){throw "Missing APK: $apk"}
& $Adb -s $Serial get-state
if($LASTEXITCODE -ne 0){throw 'Device unavailable. Connect and authorize ADB first.'}
if($Device -eq 'Quest'){
    $voice=Join-Path $env:TEMP 'TeleNao-Cori-1.13.8.apk'
    $voiceHash='1e8c733a250b78bb6b81dfefd21ca6af86d481c39705d3814930e0aafa4b7f07'
    $voiceUrl='https://huggingface.co/csukuangfj2/sherpa-onnx-apk/resolve/main/tts-engine-new/1.13.8/sherpa-onnx-1.13.8-arm64-v8a-eng-tts-engine-vits-piper-en_GB-cori-medium.apk'
    if(-not (Test-Path -LiteralPath $voice) -or (Get-FileHash -LiteralPath $voice -Algorithm SHA256).Hash.ToLowerInvariant() -ne $voiceHash){
        Write-Host 'Downloading the offline Cori voice engine (about 86 MB)...'
        Invoke-WebRequest -Uri $voiceUrl -OutFile $voice
    }
    if((Get-FileHash -LiteralPath $voice -Algorithm SHA256).Hash.ToLowerInvariant() -ne $voiceHash){throw 'Voice engine checksum mismatch'}
    & $Adb -s $Serial install -r $voice
    if($LASTEXITCODE -ne 0){throw 'Could not install Cori voice engine. Device data has not been cleared.'}
}
& $Adb -s $Serial install -r $apk
if($LASTEXITCODE -ne 0){throw 'Installation failed. Device data has not been cleared.'}
$activity='it.telenao.quest/it.telepepper.quest.LauncherActivity'
& $Adb -s $Serial shell am start -n $activity
if($LASTEXITCODE -ne 0){throw 'Installed, but could not open app. Open TeleNao on the device.'}

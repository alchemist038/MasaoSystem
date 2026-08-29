# Masao Comment Reader Control

Windows control panel for the private viewer-comment reader on INS14.

## Runtime layout

- Application: `C:\masao\comment_reader_control\masao_comment_control.pyw`
- Comment receiver: `C:\masao\comment_reader`
- Private BouyomiChan: `C:\masao\BouyomiChan_Comments_BT`
- Desktop shortcut: `まさお コメント読み上げ.lnk`

The application runs with `pythonw.exe`, so it does not open a console. The
private `BouyomiChanComments.exe` must stay open as a normal visible window.
Starting it hidden or storing it only in the task tray can prevent OBS
application-audio capture from binding reliably. The visible window also keeps
errors, queue state, and socket state observable. Closing the control window
does not stop the current reader mode; use `Stop` when the private reader itself
should stop.

While the control application is open, it checks the configured Shokz endpoint
once per second. After a Bluetooth disconnect/reconnect transition it mutes the
private OBS source, restarts only the private receiver and BouyomiChan, then
restores the previous earphones-only or earphones-plus-stream mode. It does not
start a reader that was already stopped. Automatic restart activity is written
to `C:\masao\comment_reader_control\control.log`.

## Modes

| mode | receiver | private BouyomiChan | OBS private source |
| --- | --- | --- | --- |
| Stop | stopped | stopped | muted |
| Earphones only | running | running | muted |
| Earphones + stream | running | running | unmuted |

Stopping always attempts to mute the OBS source before stopping the private
processes. The existing Taro/Goro path on ports `50000 -> 50001` is never
started, stopped, or reconfigured by this application.

The OBS source is named `コメント読み上げ（配信）`, is fixed to
`BouyomiChanComments.exe`, uses the same initial volume as the existing stream
BouyomiChan (`-13.09 dB`), and has audio monitoring disabled. When stream mode
is active, the application ensures the source exists in the current program
scene. Both OBS sources use executable-name priority because their window titles
and WinForms window classes can be identical after restart. The legacy and
private executables have different filenames.

## Deploy

```powershell
.\deploy_to_runtime.ps1
```

Deploy the related `comment_reader` folder as well when its start/stop scripts
have changed. Runtime `config.json` and `aliases.json` are preserved.

## Tests

```powershell
C:\masao_ptz\_runtime_python314\python.exe .\test_control.py
node .\obs_bridge.js status
```

# Private live-comment reader

This is the INS14-side receiver for reading all viewer comments only through the
owner's Bluetooth earphones. It is separate from the existing Taro/Goro stream
audio path.

## Fixed separation

| path | receiver | speech port | destination |
| --- | --- | --- | --- |
| Existing Taro/Goro | `C:\masao\tcp_listener.py` on `50000` | `50001` | Stream |
| Private viewer comments | `comment_reader.py` on `50002` | `50003` | Shokz; optional separate OBS source |

Never modify, restart, or replace the existing `50000 -> 50001` path while
working on this component.

## Safety behavior

The receiver drops a comment without queueing it unless all of these are true:

- the configured Shokz render endpoint is active;
- OBS Desktop Audio is saved as muted with volume zero;
- the message has a new `message_id` and is not from the owner, a bot, or a
  configured excluded channel.

The start script checks that the existing stream BouyomiChan is listening on
`50001` by reading the Windows listener table. The receiver does not connect to
the legacy port for each comment, so private reading cannot wake or disturb the
Taro/Goro BouyomiChan.

Comments received while safety is closed are remembered and never replayed as
stale backlog. The private BouyomiChan uses a renamed executable and a dedicated
port so OBS's existing `BouyomiChan.exe` process capture does not intentionally
target it. The dedicated OBS source is muted by default and is opened only by
the control application. Earphone-only and live-stream output were confirmed on
2026-08-13.

## Control application

Use the desktop shortcut `まさお コメント読み上げ` for normal operation. It
controls only the private receiver and `BouyomiChanComments.exe`.

| mode | private receiver | Shokz | OBS source |
| --- | --- | --- | --- |
| Stop | stopped | off | muted |
| Earphones only | running | on | muted |
| Earphones + stream | running | on | unmuted |

The application also provides private start, stop, restart, an earphone test,
and an emergency OBS mute. Private BouyomiChan starts with no visible window.
OBS stream output uses the separate source `コメント読み上げ（配信）`; the
existing Taro/Goro source remains unchanged. Closing the application window
does not stop the selected mode; use `Stop` to stop the private reader.

While the control application is open, a Shokz disconnect/reconnect transition
automatically restarts only the private receiver and BouyomiChan. The OBS source
is muted before restart and the previous private/stream mode is restored after
the private ports are ready.

## i5 sender contract

Send one UTF-8 JSON object per line to `100.106.183.15:50002`:

```json
{
  "message_id": "youtube-live-chat-message-id",
  "author_channel_id": "youtube-channel-id",
  "author": "display name",
  "text": "comment text",
  "message_type": "textMessageEvent",
  "published_at": "2026-08-13T12:34:56Z",
  "is_member": false,
  "is_moderator": false,
  "is_owner": false,
  "is_bot": false,
  "is_system": false
}
```

Reuse comments already fetched by V7. Do not add a second YouTube polling loop.
The i5 agent owns that sender change.

## Preparation

Run from an ordinary PowerShell window:

```powershell
.\deploy_to_runtime.ps1
.\prepare_bouyomi_bt.ps1
```

Open PowerShell as Administrator once and allow only the i5 Tailscale sender:

```powershell
C:\masao\comment_reader\install_firewall_rule.ps1
```

Connect OpenRun Pro 2, then start manually:

```powershell
C:\masao\comment_reader\start_comment_reader.ps1
```

Status and stop:

```powershell
C:\masao\comment_reader\status_comment_reader.ps1
C:\masao\comment_reader\stop_comment_reader.ps1
```

Automatic startup remains disabled. Start it manually from the desktop control
application when needed.

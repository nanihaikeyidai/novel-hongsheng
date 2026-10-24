param()

$ErrorActionPreference = 'Stop'
$wfPath = (Get-ChildItem -LiteralPath 'F:\ComfyUI_V6.0' -File -Filter '*_api.json' | Where-Object { (Get-Content -LiteralPath $_.FullName -Raw -Encoding utf8) -match '"MiniMaxH3Director"' } | Select-Object -First 1 -ExpandProperty FullName)
if ([string]::IsNullOrWhiteSpace($wfPath)) { throw 'Target MiniMax H3 director workflow was not found.' }
$inputDir = 'F:\Work-Fisher纯净包2026.8.7\ComfyUI\input'
$principalSource = 'F:\Work-Fisher纯净包2026.8.7\ComfyUI\input\redstring_ep02_s07_principal.png'
$officeSource = 'F:\Work-Fisher纯净包2026.8.7\ComfyUI\input\redstring_ep02_s07_rainy_principal_office.png'
$principalFile = 'redstring_ep02_s07_principal_v2.png'
$officeFile = 'redstring_ep02_s07_rainy_principal_office_v2.png'

Copy-Item -LiteralPath $principalSource -Destination (Join-Path $inputDir $principalFile) -Force
Copy-Item -LiteralPath $officeSource -Destination (Join-Path $inputDir $officeFile) -Force
Copy-Item -LiteralPath $wfPath -Destination ($wfPath + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json') -ErrorAction Stop

$principalVoice = 'An approximately 52-year-old Chinese male principal: mid-low chest-led voice, restrained and responsible, precise articulation, normally measured but now accelerated by fear; shallow breaths between thought units, never hysterical, never youthful, never theatrical.'
$ndVoice = 'An adult Chinese male ND emergency coordinator: low, even chest resonance, calm professional diction, medium-fast procedural pace, controlled volume and clean consonants; never sarcastic, never panicked, never emotionally flat.'

function Convert-UnicodeEscapes([string]$value) { return [regex]::Unescape($value) }
function New-Prompt([string]$unit,[string]$direction,[string]$exit,[string]$voiceBlock) {
@"
subject_definitions:
<Subject 1> is the principal from <Picture 1>: approximately 52 years old, black-grey short hair, rectangular glasses, charcoal suit, pale shirt and dark tie. <Picture 1> preserves identity, face, age, build and wardrobe only; not its white background or pose. He is the only visible human, his collar is damp and he is visibly tense. $principalVoice
<Subject 2> is the rainy principal's office from <Picture 2>: dark wood desk, fixed black landline on the desk's left-front, monitor on the desk, filing cabinets behind, rain-streaked window to screen-right, cold blue-grey rainy daylight. <Picture 2> preserves spatial layout and atmosphere only; not photographic texture, readable seals, text or logos.
The off-screen ND coordinator (S2) is audio-only and never has a visible body, face, avatar, mouth movement or video-call interface. $ndVoice

summary:
[reference generation] Generate $unit of one continuous 15-second 16:9 horizontal 2K-class high-detail Japanese anime cinematic scene. No first frame, storyboard, reference audio or reference video. The principal is already on an active landline call inside his rainy office. The scene is dialogue-led and ends on a stable phone-call pose.

retention_analysis:
<Subject 1>: fully_preserved - retain the principal's identity, glasses, charcoal suit, damp collar, anxiety and the receiver against his right ear.
<Subject 2>: fully_preserved - retain the desk, fixed landline, cabinets, rain-streaked window, cold blue-grey rain light and empty office.
The ND coordinator: reference - retain only the specified telephone voice; never render the caller.

detailed_description:
High-detail Japanese anime cinematic style: delicate cel-shaded adult character, hand-drawn office background, stable clean linework, cold blue-grey rainy ambient light, rain-streaked glass and restrained wet reflections. Fixed 180-degree axis: cabinets at screen-left, principal seated behind desk center, rainy window at screen-right. The principal holds the black landline receiver to his right ear; its cord lies naturally across the desk. Only the principal is visible.

[Shot 1] At 00:00.000, stable side-medium shot from the principal's left. $direction
$voiceBlock

[Shot 2] At 00:07.000, cut to a close three-quarter view that keeps the principal's mouth, glasses and receiver visible. He listens with his jaw held tight, then reacts only after the previous voice ends; no simultaneous speech, no visible mouth movement for audio-only speech.

[Shot 3] At 00:11.500, return to the stable side-medium composition. $exit Hold the final composition without a new action from 14.20 seconds through 15.00 seconds.

No subtitles, captions, on-screen text, Chinese characters, title cards, speech bubbles, UI, watermark, logo, readable email, readable monitor content, video-call avatar, or a second visible human.

overall_soundscape:
Rain against the window, low room tone, faint telephone-line texture, receiver and cord handling, the principal's shallow breath, and strictly sequential dialogue only. No narration, crowd sound, monster sound, monitor replay, extra dialogue, score or music.

non_diegetic_music:
None. No BGM, no score, no theme music, no musical sting, and no non-diegetic audio.

## negativePrompt
subtitles, captions, on-screen text, Chinese characters, title cards, speech bubbles, UI, interface overlay, readable email, readable monitor content, surveillance replay, monster, bat creature, video-call avatar, second visible human, off-screen caller visible, wrong lip sync, principal speaking the caller line, caller mouth movement, watermark, logo, camera shake, motion blur, unstable final frame, photorealism, live action, 3D render, Western comic, childish cartoon, oil painting, sunny weather, warm sunlight, BGM, score.

## Continuity Exit
$exit
"@
}

$d07 = Convert-UnicodeEscapes 'He begins speaking immediately, fast but intelligible. <Subject 1> (S1)<d>[Chinese] \u004e\u0044\u5417\uff1f\u6211\u6821\u906d\u9047\u4e0d\u660e\u5de8\u578b\u751f\u7269\u88ad\u51fb\u3002\u76d1\u63a7\u89c6\u9891\u5df2\u53d1\u7814\u7a76\u6240\u5b98\u65b9\u90ae\u7bb1\u3002</d> Exact lip sync; one quick breath at the sentence break.'
$e07 = 'Exit state: receiver pressed to right ear, left hand braced on desk, mouth closed, waiting for reply.'
$d08 = Convert-UnicodeEscapes 'Open on the exact same pose. <Subject 1> (S1)<d>[Chinese] \u80fd\u786e\u5b9a\u5b83\u662f\u4ec0\u4e48\u5417\uff1f</d> Exact lip sync, then he listens.'
$e08 = 'Exit state: receiver at right ear, principal leans forward, left hand grips desk edge, mouth closed.'
$v08 = Convert-UnicodeEscapes 'Audio-only ND coordinator (S2)<d>[Chinese] \u5148\u786e\u8ba4\uff1a\u6709\u65e0\u4eba\u5458\u4f24\u4ea1\uff1f</d> The visible principal keeps lips closed. Then <Subject 1> (S1)<d>[Chinese] \u6682\u65e0\u4f24\u4ea1\u3002\u5b66\u751f\u90fd\u64a4\u51fa\u6765\u4e86\u3002</d> Exact lip sync.'
$d09 = Convert-UnicodeEscapes 'Open on the same seated pose. <Subject 1> (S1)<d>[Chinese] \u5b83\u649e\u8fdb\u6559\u5ba4\uff0c\u5dee\u70b9\u4f24\u5230\u5b69\u5b50\u3002\u5b83\u8fd8\u4f1a\u51fa\u73b0\u5417\uff1f</d> Exact lip sync; the final question escapes faster.'
$e09 = 'Exit state: receiver fixed to right ear, principal seated still, left hand clenched on desk edge, mouth closed.'
$v09 = Convert-UnicodeEscapes 'Only after the principal finishes, audio-only ND coordinator (S2)<d>[Chinese] \u73b0\u573a\u5148\u5c01\u9501\uff0c\u6240\u6709\u4eba\u4e0d\u5f97\u9760\u8fd1\u3002</d> The visible principal listens with lips closed.'
$d10 = Convert-UnicodeEscapes 'Open on the exact same pose. Audio-only ND coordinator (S2)<d>[Chinese] \u76d1\u63a7\u539f\u4ef6\u4e0d\u8981\u526a\u8f91\u3001\u4e0d\u8981\u5916\u4f20\u3002\u6211\u4eec\u7684\u4eba\u6b63\u5728\u8d76\u5f80\u73b0\u573a\u3002</d> The visible principal keeps lips closed.'
$e10 = 'Exit state: receiver against right ear, principal faces the rain-dark window, mouth closed, no new movement.'
$v10 = Convert-UnicodeEscapes 'After the caller finishes, <Subject 1> (S1)<d>[Chinese] \u5b83\u5230\u5e95\u662f\u4ec0\u4e48\uff1f</d> Exact lip sync. Audio-only ND coordinator (S2)<d>[Chinese] \u76ee\u524d\u65e0\u6cd5\u786e\u8ba4\u3002</d> The principal does not speak again.'
$p07 = New-Prompt -unit 'EP02-P07' -direction $d07 -exit $e07 -voiceBlock ''
$p08 = New-Prompt -unit 'EP02-P08' -direction $d08 -exit $e08 -voiceBlock $v08
$p09 = New-Prompt -unit 'EP02-P09' -direction $d09 -exit $e09 -voiceBlock $v09
$p10 = New-Prompt -unit 'EP02-P10' -direction $d10 -exit $e10 -voiceBlock $v10

$data = Get-Content -Raw -Encoding utf8 $wfPath | ConvertFrom-Json
$data.'2'.inputs.clip_name = 'qwen3vl_32b_minimax_h3_int8_convrot.safetensors'
$data.'24'.inputs.lora_name = 'h3\minimax_h3_fl2v_turbo_4step_v1.1_768p_comfyui_bf16.safetensors'
$timeline = $data.'12'.inputs.timeline_data | ConvertFrom-Json
$refs = @(
    [pscustomobject]@{ index = 0; imageFile = $principalFile; fileName = $principalFile; type = 'input'; subfolder = '' },
    [pscustomobject]@{ index = 1; imageFile = $officeFile; fileName = $officeFile; type = 'input'; subfolder = '' }
)
$prompts = @($p07,$p08,$p09,$p10)
$segments = @()
for ($i=0; $i -lt 4; $i++) {
    $segments += [pscustomobject]@{ id=('ep02_p{0:00}' -f (7+$i)); name=('EP02-P{0:00}' -f (7+$i)); startFrame=($i*362); length=362; frameCount=362; duration=15; prompt=$prompts[$i]; negativePrompt='subtitles, captions, on-screen text, Chinese characters, title cards, speech bubbles, UI, watermark, logo, readable text, monster, surveillance replay, video-call avatar, caller visible, second visible human, BGM'; taskType='r2v'; refs=@(); refAudios=@(); refVideos=@(); genImage=[pscustomobject]@{imageFile='';fileName=''}; continuityFromPrev=($i -gt 0); refImageSize='match'; referenceVideo=[pscustomobject]@{videoFile='';fileName='';type='input';subfolder=''} }
}
$timeline.batchWorkspaces.r2v.globalCommon.refs = @($refs)
$timeline.batchWorkspaces.r2v.globalCommon.refAudios = @()
$timeline.batchWorkspaces.r2v.globalCommon.refVideos = @()
$timeline.batchWorkspaces.r2v.globalCommon.prompt = 'Global references: Picture 1 is the principal identity sheet; Picture 2 is the rainy principal office. Both retain only their stated visual identity and environment anchors. No first-frame image, no storyboard, no audio reference, no video reference. All four sequential 15-second units depict one phone call in one rainy office; no monitor replay or visible caller.'
$timeline.segments = @($segments)
$timeline.batchWorkspaces.r2v.segments = @($segments)
$timeline.totalFrames = 1448
$timeline.frameRate = 24
$data.'12'.inputs.timeline_data = $timeline | ConvertTo-Json -Depth 100 -Compress
$data.'12'.inputs.total_frames = 1448
$data.'12'.inputs.frame_rate = 24
$data.'12'.inputs.width = 1376
$data.'12'.inputs.height = 768
$data | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $wfPath -Encoding utf8

$verify = Get-Content -Raw -Encoding utf8 $wfPath | ConvertFrom-Json
$vt = $verify.'12'.inputs.timeline_data | ConvertFrom-Json
if ($vt.segments.Count -ne 4 -or $vt.batchWorkspaces.r2v.segments.Count -ne 4 -or $verify.'12'.inputs.total_frames -ne 1448 -or $vt.totalFrames -ne 1448) { throw 'Timeline validation failed.' }
for ($i=0; $i -lt 4; $i++) { if ($vt.segments[$i].startFrame -ne ($i*362) -or $vt.segments[$i].length -ne 362 -or [string]::IsNullOrWhiteSpace($vt.segments[$i].negativePrompt)) { throw "Segment validation failed: $i" } }
[pscustomobject]@{ Workflow=$wfPath; Segments=$vt.segments.Count; Frames=$vt.totalFrames; FPS=$vt.frameRate; Refs=($vt.batchWorkspaces.r2v.globalCommon.refs.imageFile -join ','); Hash=(Get-FileHash -Algorithm SHA256 $wfPath).Hash } | Format-List

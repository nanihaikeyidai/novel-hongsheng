param(
    [string]$ApiPath = 'F:\ComfyUI_V6.0\MiniMax H3 导演台全能工作流_api.json',
    [string]$ComfyInput = 'F:\Work-Fisher纯净包2026.8.7\ComfyUI\input'
)

$ErrorActionPreference = 'Stop'
$root = 'D:\HermesWorkspace\ai小说\红绳'
$assets = @(
    @{ Source = Join-Path $root '05-workflow\ep02\归档素材\人物\校长_人设.png'; Target = 'redstring_ep02_s07_principal.png' },
    @{ Source = Join-Path $root '05-workflow\ep02\归档素材\怪物\黑翼飞行怪兽.png'; Target = 'redstring_ep02_s07_bat_distortion.png' },
    @{ Source = Join-Path $root '05-workflow\ep02\归档素材\场景\场景_雨天校长办公室_无人.png'; Target = 'redstring_ep02_s07_rainy_principal_office.png' }
)

foreach ($asset in $assets) {
    if (-not (Test-Path -LiteralPath $asset.Source -PathType Leaf)) { throw "缺少参考素材：$($asset.Source)" }
}
if (-not (Test-Path -LiteralPath $ApiPath -PathType Leaf)) { throw "找不到导演台 API：$ApiPath" }
if (-not (Test-Path -LiteralPath $ComfyInput -PathType Container)) { throw "找不到 ComfyUI input 目录：$ComfyInput" }

$prompt = @'
subject_definitions:
<Subject 1> is the principal from <Picture 1>: an approximately 52-year-old adult male school principal with short black-grey hair, rectangular glasses, a dark charcoal-grey suit, light shirt and tie. <Picture 1> locks only his identity, face, age, proportions and clothing; it does not supply a background or pose. In this segment he is visibly sweating, his collar is damp, and he is the only visible human. He speaks only as (S3).
<Subject 2> is the giant bat-like distorted creature from <Picture 2>, with a grey-black body, broad black wings, pointed ears and red eyes. <Picture 2> locks its silhouette and surface traits only. It appears exclusively as an abstract surveillance replay inside the monitor and never enters the principal's office.
<Subject 3> is the rainy principal's office from <Picture 3>. <Picture 3> locks the monitor desk, fixed landline, filing cabinets, rain-streaked window, desk layout and cold blue-grey rain light; it does not transfer photographic texture, readable wall marks or temporary people.
<Subject 4> is an audio-only school secretary: an off-screen adult female intercom voice (S1), never visible and never given a body, face, avatar or lip movement.
<Subject 5> is an audio-only ND emergency coordinator: an off-screen adult male telephone voice (S2), low, calm and authoritative, never visible and never given a body, face, avatar or lip movement.

summary:
[reference generation] Generate one continuous 15-second, 16:9 horizontal, 2K-class anime-film scene from three reference images. In the rainy principal's office, <Subject 1> reviews a surveillance replay of <Subject 2>, receives a short intercom notice from <Subject 4>, answers the ringing landline, and completes one concise emergency exchange with <Subject 5>. The clip ends with <Subject 1> holding the receiver to his right ear, ready to continue the call in the next segment. No first frame, storyboard image, reference audio or reference video is used.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2], [Shot 3], [Shot 4]): fully_preserved - preserve his adult principal identity, glasses, black-grey hair, charcoal suit and mounting sweat; allow only the scripted seated monitoring, head turn, receiver pickup and spoken response.
<Subject 2> (appears only inside the monitor in [Shot 2]): fully_preserved - preserve the bat-like silhouette, black wings and grey-black body only as surveillance imagery; never materialize it in the office.
<Subject 3> (appears in [Shot 1], [Shot 2], [Shot 3], [Shot 4]): fully_preserved - preserve the office layout, monitor desk, landline, cabinets, rain-streaked window and cold blue-grey atmosphere; convert the source to the project's hand-drawn anime-film visual language.
<Subject 4>: fully_preserved - retain only one brief off-screen female secretary announcement; no visual representation exists.
<Subject 5>: fully_preserved - retain only one off-screen male ND emergency inquiry through the telephone; no visual representation exists.

detailed_description:
The target video is a high-detail Japanese anime youth cinematic scene with delicate cel-shaded characters, hand-drawn animation backgrounds, clean stable linework, transparent atmospheric perspective, cold blue-grey rainy ambient light, rain-streaked glass and restrained wet reflections. The fixed world axis is filing cabinets -> principal seated behind monitor desk -> monitor -> rainy window. The landline sits within his right-hand reach. Only <Subject 1> is visible; <Subject 4> and <Subject 5> remain strictly audio-only, and <Subject 2> remains confined to the monitor image.

[Shot 1] At 00:00.000, a stable medium close shot shows <Subject 1> alone at <Subject 3>'s monitor desk. He repeatedly drags an unreadable abstract replay marker, breathing fast, while pale monitor light crosses his sweaty side profile. Through the office intercom, <Subject 4> (S1) says, <d>[Chinese] 校长，教育局转来专线。</d> The principal's lips stay closed; after the announcement ends, the intercom falls silent and no speaker appears.

[Shot 2] At 00:02.500, cut to the monitor in fixed close view. <Subject 2> exists only within the abstract surveillance replay, smashing through a rainy classroom window as black wings and glass fragments sweep across the monitor image. No timestamp, text or real UI is visible. Cut back to the principal's eyes: his pupils tighten and he leans toward the screen.

[Shot 3] At 00:05.500, a stable side-medium desk shot. The landline rings and vibrates slightly. <Subject 1> flinches once, picks up the receiver with his right hand, and presses it to his right ear; the cord straightens naturally across the desk. Once the receiver reaches his ear and he has closed his lips, <Subject 5> (S2) says, <d>[Chinese] 这里是ND应急处置组。现场有无人员伤亡？</d> The caller remains unheard after the line ends and never appears.

[Shot 4] At 00:10.500, keep the same side-medium composition. <Subject 1> continues looking toward the monitor, jaw tense and breathing shallow. After <Subject 5> has finished and the line is silent, <Subject 1> (S3) says with precise visible lip sync, <d>[Chinese] 没有，学生都撤出来了。</d> He closes his mouth after the final syllable, grips the receiver more tightly, and becomes still by 14.50 seconds. Hold at least 0.50 seconds on the stable exit state: receiver against his right ear, eyes fixed on the monitor, rain continuing outside, landline cord resting on the desk, no new action.

No subtitles, captions, Chinese characters, title cards, speech bubbles, UI, watermark or logo appear in the image. No visible text or real surveillance interface appears on the monitor.

overall_soundscape:
Continuous rain against the window, a low monitor hum, the principal's quick breathing, one short intercom transmission, one brief landline ring and vibration, receiver and cord handling sounds, then three strictly sequential voices with silence between each speaker. No crowd, narration, added effects or background music.

non_diegetic_music:
N/A
'@

$negativePrompt = 'subtitles, captions, on-screen text, Chinese characters, title cards, speech bubbles, UI, watermark, logo, readable text, real surveillance UI, timestamps, report text, storyboard grid, panel borders, numbers, arrows, production annotations, second visible person, secretary on screen, ND coordinator on screen, caller face, caller avatar, caller mouth, video-call window, creature physically inside the office, creature leaving the monitor, extra creature, duplicate principal, identity drift, wrong age, wrong clothing, missing glasses, sweat disappearing, floating telephone, broken phone cord, prop teleportation, spatial flip, axis crossing, camera shake, sudden zoom, motion blur, unstable final frame, photorealistic, live action, 3D render, Western comic, childish cartoon, oil painting, sunny weather, warm sunlight, background music, BGM'

$backupPath = Join-Path (Split-Path -Parent $ApiPath) (([IO.Path]::GetFileNameWithoutExtension($ApiPath)) + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
Copy-Item -LiteralPath $ApiPath -Destination $backupPath -ErrorAction Stop
foreach ($asset in $assets) {
    Copy-Item -LiteralPath $asset.Source -Destination (Join-Path $ComfyInput $asset.Target) -Force
}

$workflow = Get-Content -Raw -Encoding UTF8 $ApiPath | ConvertFrom-Json
$timeline = $workflow.'12'.inputs.timeline_data | ConvertFrom-Json
$refs = @()
for ($index = 0; $index -lt $assets.Count; $index++) {
    $fileName = $assets[$index].Target
    $refs += [pscustomobject]@{ index = $index; imageFile = $fileName; fileName = $fileName; type = 'input'; subfolder = '' }
}
$segment = [pscustomobject]@{
    id = 'ep02_segment07_principal_emergency_line_15s'
    start = 0
    length = 362
    frameCount = 362
    durationSec = 15
    prompt = $prompt
    negativePrompt = $negativePrompt
    taskType = ''
    refs = @()
    refAudios = @()
    refVideos = @()
    genImage = [pscustomobject]@{ imageFile = ''; fileName = '' }
    continuityFromPrev = $false
    refImageSize = 'match'
}
$batchSegment = $segment | ConvertTo-Json -Depth 20 | ConvertFrom-Json
$batchSegment | Add-Member -NotePropertyName referenceVideo -NotePropertyValue ([pscustomobject]@{ videoFile=''; fileName=''; type='input'; subfolder='' })

$timeline.editMode = 'segment'
$timeline.totalFrames = 362
$timeline.frameRate = 24
$timeline.durationSec = 15
$timeline.video.sourceFrameCount = 362
$timeline.global.taskType = 'r2v — 参考主体生视频(Reference to Video)'
$timeline.global.prompt = $prompt
$timeline.global.refs = $refs
$timeline.global.refAudios = @()
$timeline.global.refVideos = @()
$timeline.segments = @($segment)
$timeline.keyframes = @()
$timeline.shots = @()
$timeline.runSelectEnabled = $true
$timeline.runSelection = @(0)
$timeline.width = 1376
$timeline.height = 768
$timeline.refMaxSize = 1376
$timeline.batchWorkspaces.r2v.globalCommon.prompt = $prompt
$timeline.batchWorkspaces.r2v.globalCommon.refs = $refs
$timeline.batchWorkspaces.r2v.globalCommon.refAudios = @()
$timeline.batchWorkspaces.r2v.globalCommon.refVideos = @()
$timeline.batchWorkspaces.r2v.segments = @($batchSegment)
$timeline.batchWorkspaces.r2v.runSelectEnabled = $true
$timeline.batchWorkspaces.r2v.runSelection = @(0)
$timeline.batchWorkspaces.r2v.selectedIndex = 0

$workflow.'12'.inputs.task_type = 'r2v — 参考主体生视频(Reference to Video)'
$workflow.'12'.inputs.global_prompt = $prompt
$workflow.'12'.inputs.width = 1376
$workflow.'12'.inputs.height = 768
$workflow.'12'.inputs.frame_rate = 24
$workflow.'12'.inputs.total_frames = 362
$workflow.'12'.inputs.ref_max_size = 1376
$workflow.'12'.inputs.timeline_data = $timeline | ConvertTo-Json -Depth 100 -Compress

$serialized = $workflow | ConvertTo-Json -Depth 100
$checkWorkflow = $serialized | ConvertFrom-Json
$checkTimeline = $checkWorkflow.'12'.inputs.timeline_data | ConvertFrom-Json
if ($checkTimeline.segments.Count -ne 1 -or $checkTimeline.batchWorkspaces.r2v.segments.Count -ne 1 -or $checkTimeline.totalFrames -ne 362 -or $checkTimeline.frameRate -ne 24 -or $checkTimeline.segments[0].length -ne 362 -or $checkTimeline.segments[0].durationSec -ne 15 -or $checkTimeline.segments[0].negativePrompt -ne $checkTimeline.batchWorkspaces.r2v.segments[0].negativePrompt -or @($checkTimeline.global.refs).Count -ne 3 -or @($checkTimeline.global.refAudios).Count -ne 0 -or $checkWorkflow.'12'.inputs.global_prompt -ne $checkTimeline.global.prompt -or $checkTimeline.global.prompt -ne $checkTimeline.batchWorkspaces.r2v.globalCommon.prompt) { throw '导演台 API 校验失败，未写入修改。' }
[IO.File]::WriteAllText($ApiPath, $serialized, [Text.UTF8Encoding]::new($false))
Write-Output "BACKUP=$backupPath"
Write-Output "API_UPDATED=$ApiPath"
Write-Output "INPUTS_COPIED=$ComfyInput"

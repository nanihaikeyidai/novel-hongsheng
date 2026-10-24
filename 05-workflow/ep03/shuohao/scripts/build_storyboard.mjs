import fs from 'node:fs';
import path from 'node:path';

const root = 'D:/HermesWorkspace/ai小说/红绳';
const ep = path.join(root, '05-workflow', 'ep03');
const out = path.join(ep, 'shuohao', 'storyboard');
const active = ep;
fs.mkdirSync(out, { recursive: true });

const people = {
  C01: '05-workflow/ep03/归档素材/人物/安娜_游泳社人设.png',
  C02: '05-workflow/ep03/归档素材/人物/李想_游泳社人设.png',
};
const commonNegative = '禁止字幕、禁止画面文字、禁止中文字符、禁止标题卡、禁止对话气泡、禁止UI、禁止水印、禁止额外Logo、禁止摄影写实、禁止3D渲染、禁止欧美漫画、禁止低幼卡通、禁止泳池水中出现无关人物、禁止改变角色发型和服装。';

const segments = [
  { id:'E03-01', sceneIndex:1, title:'校门奔入与传闻', setting:'晴朗早晨的红杉高中正门，开学人流正常，中央校徽和校名牌可见。', chars:['C05'], props:['P01'], beats:[1,7], refs:['05-workflow/ep03/归档素材/场景/场景_红杉高中校门_晴天_无人.png'], dialogue:['等等我！听说那东西又出现了！','你说的是前几天袭击学校的那个？'], shots:['大远景：几名背书包的学生从街角跑向正门，校门和红杉树完整入画。','全景：学生冲入校门，阳光照亮校徽与校名牌，人流保持正常秩序。','中景：学生乙追上学生甲，伸手按住他的手臂，边走边压低声音。','近景：学生甲回头看向校外，神情兴奋又害怕，背景是校门铁栏。','全景：安娜尚未入画，学生群沿校园道路继续向内移动。','特写：校门上方校徽被阳光照亮，传闻声从画外继续。'] },
  { id:'E03-02', sceneIndex:1, title:'封锁带与安娜经过', setting:'校门内公告栏和远处被封锁的教学楼入口，晴天，人流从安娜身边经过。', chars:['C01','C05'], props:['P01'], beats:[8,14], refs:[people.C01,'05-workflow/ep03/归档素材/场景/场景_红杉高中校门_晴天_无人.png'], dialogue:['小声点，学校说只是设备事故。','设备事故能把窗户撕成那样？','她就是那天在附近的人吧？'], shots:['中景：学生乙把学生甲的手按下，公告栏上的恢复上课通知在后方。','全景：几名学生停在公告栏前拍照，远处教学楼入口仍有封锁带。','近景：学生甲盯着封锁带，其他学生回头交换眼神。','中景：安娜从人群外侧走来，校服整齐，书包贴在身侧。','跟拍中景：安娜听见身后议论，却不回头，步伐速度不变。','远景：上课铃响，人群分散，安娜穿过树影走向体育馆。'] },
  { id:'E03-03', sceneIndex:2, title:'室内泳池集合', setting:'明亮蓝白天光的室内标准泳池，六条空泳道，学生从侧门进入集合。', chars:['C01','C03','C05'], props:['P02','P03','P04'], beats:[1,6], refs:[people.C01,'05-workflow/ep03/归档素材/场景/场景_室内标准泳池_无人.png','05-workflow/ep03/归档素材/道具/游泳社训练套件.png'], dialogue:['所有人先站到池边，检查泳帽和泳镜。','今天做自由泳计时，不比蛮力。'], shots:['大远景：室内泳池侧门打开，学生成组进入，空泳道延伸到远端。','全景：学生把毛巾放到长椅上，蓝白天光落在水面。','中景：体育老师拿记录板和哨子站在池边，抬手示意集合。','近景：学生们检查泳镜与泳帽，动作整齐但各自为主。','中景：老师在记录板上写下测试顺序，学生群安静下来。','特写：哨子和记录板在老师手中，水声作为背景。'] },
  { id:'E03-04', sceneIndex:2, title:'李想的记录保持者', setting:'室内泳池池边，李想从学生群中走出，其他学生围在蓝色防滑垫后。', chars:['C02','C03','C04','C05'], props:['P02','P04'], beats:[7,12], refs:[people.C02,'05-workflow/ep03/归档素材/场景/场景_室内标准泳池_无人.png','05-workflow/ep03/归档素材/道具/泳池计时牌与记录板.png'], dialogue:['老师，李想是不是不用测了？','红杉高中记录保持者，早就该单独计时。','别急，记录不是拿来摆着看的。'], shots:['中景：李想从学生群里走出，把泳镜推到额头，享受视线。','近景：起哄男生故意提高音量，学生群转头看李想。','全景：李想拍肩，周围学生笑着让出通道。','近景：李想露出得意笑，记录板和泳池计时牌在背景。','中景：安娜位于队伍末端整理外套，完全没有参与笑声。','特写：安娜的手把泳帽边缘压平，动作冷静、准确。'] },
  { id:'E03-05', sceneIndex:2, title:'下一组自由泳', setting:'泳池起跳端之前的池边，老师将安娜和李想安排到相邻泳道。', chars:['C01','C02','C03','C04','C05'], props:['P03','P05'], beats:[13,18], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_室内泳池起跳端_无人.png'], dialogue:['安娜，你也下这一组吗？','老师安排了，我就下。','下一组，自由泳准备。'], shots:['中景：起哄男生把话题转向队伍末端的安娜。','近景：安娜抬眼确认老师手势，再看向相邻空泳道。','中景：安娜平直回答，身后学生群退到蓝色防滑垫后。','全景：老师将两人安排到相邻泳道，空泳道保持清晰。','跟拍中景：李想先走向右侧泳道，安娜走向左侧泳道。','远景：老师举起哨子，池边学生沿起跳端排成半弧。'] },
  { id:'E03-06', sceneIndex:3, title:'正对泳道的起跳端', setting:'室内泳池起跳端，六个起跳台在每条泳道正前方，水面无人在水中。', chars:['C01','C02','C05'], props:['P05'], beats:[1,6], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_室内泳池起跳端_无人.png'], dialogue:['校运会记录保持者来了！','红杉菲尔普斯不会输给女生吧？'], shots:['大远景：六个起跳台整齐正对六条泳道，池水干净，水里没有人。','全景：安娜和李想分别站上相邻跳台，学生群在池边围观。','中景：起哄男生从池边大声喊话，手指向李想。','近景：起哄男生夸张地比出泳道方向，学生群笑起来。','近景：李想低头确认泳镜，抬头看向安娜。','双人中景：两人并排站在正对泳道的跳台上，位置关系稳定。'] },
  { id:'E03-07', sceneIndex:3, title:'让女生先游一半', setting:'起跳台近景与池边反应，安娜保持无感，李想继续炫耀。', chars:['C01','C02','C03','C04','C05'], props:['P03','P05'], beats:[7,11], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_室内泳池起跳端_无人.png'], dialogue:['我觉得让女生先游一半，会比较公平。','安静。听口令，不许抢跳。'], shots:['近景：李想抬起下巴，面向安娜说出让半程的挑衅。','全景：池边男生用手比出半程距离，学生群夸张起哄。','特写：安娜低头检查跳台防滑面，不看李想。','中景：安娜抬眼确认远端终点池壁，表情没有变化。','中景：体育老师向前一步抬手压住笑声，恢复课堂秩序。','特写：安娜的脚稳稳踩在跳台前沿，准备姿势开始形成。'] },
  { id:'E03-08', sceneIndex:3, title:'哨响前的半拍', setting:'起跳台，安娜和李想同时进入出发姿势，发令哨即将响起。', chars:['C01','C02','C03'], props:['P03','P05'], beats:[12,16], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/道具/体育老师哨子.png','05-workflow/ep03/归档素材/场景/场景_室内泳池起跳端_无人.png'], dialogue:['跟不上也正常，别有压力。','各就各位。'], shots:['近景：李想侧过脸继续说话，语气仍然居高临下。','特写：安娜双手放到跳台前沿，没有任何回应。','双人中景：李想被安娜的安静影响，跟着俯身扣住跳台边缘。','中景：体育老师举起哨子，全场视线集中到两条泳道。','特写：哨子贴近老师嘴边，空气短暂安静。','动作特写：哨声响起，安娜先蹬离跳台，李想还停在观察的半拍。'] },
  { id:'E03-09', sceneIndex:4, title:'安娜低水花入水', setting:'室内标准泳池两条相邻泳道，安娜已经入水，李想还站在跳台上。', chars:['C01','C02'], props:['P05','P06'], beats:[1,7], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_室内标准泳池_无人.png'], dialogue:['快下去吧！还看什么？','等等，我还没——'], shots:['侧面中景：安娜俯身入水，水花压低，身体沿泳道线滑行。','水面近景：安娜的手臂从水下前伸，泳道线在身下笔直延伸。','全景：李想仍站在跳台上低头观察，得意表情还未收回。','中景：起哄男生从池边伸脚，轻轻踢中李想小腿。','动作全景：李想双臂挥动，从跳台边缘横着滑下。','低机位近景：李想拍进水里，水花遮住画面下半部。'] },
  { id:'E03-10', sceneIndex:4, title:'从笑声到追赶', setting:'泳池中段，安娜领先，李想狼狈起身后开始追赶，学生沿池边移动。', chars:['C01','C02','C04','C05'], props:['P06'], beats:[8,14], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_室内标准泳池_无人.png'], dialogue:['她怎么已经到那里了？','喂，等等我！'], shots:['全景：池边学生因李想落水同时后退，笑声爆发。','水面中景：安娜已游出第一段，动作稳定，身后没有回头。','近景：起哄男生看向安娜，笑声变成惊讶。','中景：李想从水里抬头，泳镜歪到一边。','特写：李想把泳镜按回眼前，表情第一次变认真。','跟拍中景：李想压低身体加速追赶，安娜在前方拉开距离。'] },
  { id:'E03-11', sceneIndex:4, title:'动作线与呼吸节奏', setting:'泳池中段到后半程，老师沿池边移动，安娜节奏稳定，李想开始吃力。', chars:['C01','C02','C03'], props:['P06'], beats:[15,21], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_室内标准泳池_无人.png'], dialogue:['保持身体线，别抬头！'], shots:['侧面跟拍：体育老师沿池边跟着两条泳道移动。','水下中景：安娜手臂交替划水，身体线保持平直。','近景：李想提高划水频率，水花明显变大。','中景：老师观察两人的肩线和换气，手中记录板贴在身侧。','远景：安娜越过泳道中段标记，李想仍在后方。','特写：安娜平稳换气后重新把脸压入水面。'] },
  { id:'E03-12', sceneIndex:4, title:'终点池壁', setting:'泳道远端终点，安娜先触壁，李想明显落后，计时牌亮起。', chars:['C01','C02','C03','C04','C05'], props:['P02','P06'], beats:[22,28], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_室内标准泳池_无人.png','05-workflow/ep03/归档素材/道具/泳池计时牌与记录板.png'], dialogue:['李想，别光顾着耍帅！','安娜第一，李想第二。','这不是赢一点吧？'], shots:['远景：起哄男生沿池边跑着喊，李想仍锁定终点。','全景：安娜接近终点池壁，水线在她身后拉长。','动作近景：安娜先一步伸手碰壁，掌心稳稳按住池沿。','特写：计时牌亮起，体育老师低头记数。','全景：李想几秒后撞上池壁，学生群的笑声变成议论。','近景：安娜推起泳镜，扫过计时牌后低头看自己的手指。'] },
  { id:'E03-13', sceneIndex:5, title:'成绩超过记录', setting:'泳池边休息区，学生上岸恢复训练，李想从池中上岸查看记录。', chars:['C01','C02','C03','C05'], props:['P02','P04'], beats:[1,7], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_泳池边休息区_无人.png','05-workflow/ep03/归档素材/道具/泳池计时牌与记录板.png'], dialogue:['你刚才，游了多少次？','忘了。','这个成绩，比校运会记录快。'], shots:['全景：学生们陆续上岸，拿起毛巾和水杯，池边恢复普通训练声。','中景：安娜拧干发梢，把泳镜放进训练袋。','近景：李想沿梯子上岸，喘息后看向安娜。','双人中景：李想站在安娜身后几步，认真问她训练经历。','近景：安娜只说忘了，语气平直，拧毛巾的动作不停。','特写：李想接过记录板，核对计时数字，神情转为郑重。'] },
  { id:'E03-14', sceneIndex:5, title:'正式邀请', setting:'泳池边长椅，李想从长椅下拿出空白游泳部报名表，安娜接过。', chars:['C01','C02','C04'], props:['P07'], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/道具/游泳部报名表_无字.png'], beats:[8,14], dialogue:['哦。','我正式邀请你加入游泳部。','不是缺人，也不是临时凑数。'], shots:['近景：安娜听到超过记录，只平淡地说哦。','中景：李想把记录板递回老师，转身走向长椅。','动作特写：李想从长椅下拿出空白报名表。','双人中景：李想站直，把报名表递向安娜。','近景：起哄男生想插话，李想抬手把他挡回去。','中景：安娜接过报名表，李想认真说明邀请不是凑数。'] },
  { id:'E03-15', sceneIndex:5, title:'我会看看', setting:'泳池边休息区，安娜检查报名表内容，只问训练频率和不参加的后果。', chars:['C01','C02'], props:['P07'], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_泳池边休息区_无人.png','05-workflow/ep03/归档素材/道具/游泳部报名表_无字.png'], beats:[15,22], dialogue:['每天都训练？','基本每天，周末看安排。','不去会怎样？','不会怎样，只是错过训练。'], shots:['近景：安娜看报名表上的训练时间，眼神只在项目之间移动。','双人中景：她问每天是否训练，李想立刻解释安排。','特写：安娜把报名表翻到背面，检查是否有附加条件。','近景：安娜问不去的后果，语气像在确认退出成本。','中景：李想认真回答，不再用玩笑施压。','远景：安娜看向泳池，学生已回到各自泳道，水面被划水声打碎。'] },
  { id:'E03-16', sceneIndex:5, title:'没有拒绝的邀请', setting:'泳池边通往更衣室的入口，安娜收起报名表，李想和起哄男生留在池边。', chars:['C01','C02','C03','C04','C05'], props:['P03','P07'], refs:[people.C01,people.C02,'05-workflow/ep03/归档素材/场景/场景_泳池边休息区_无人.png','05-workflow/ep03/归档素材/道具/游泳部报名表_无字.png'], beats:[23,30], dialogue:['所以，你愿意来吗？','我会看看。','那就是没拒绝？','你邀请了我。','她到底算不算加入？','她说会看看。','下一次，我不会再让你提前半程。'], shots:['双人中景：李想收起炫耀，小心问安娜愿不愿意来。','特写：安娜把报名表对折，停顿后说会看看；李想愣住，起哄男生从旁边探头确认。','动作特写：安娜把报名表放进口袋，表情没有承诺意味。','中景：安娜走向更衣室入口，李想没有伸手拦。','远景：安娜在门口停半步但不回头，李想对男生重复她的回答。','全景：李想对安娜背影宣布下次不让半程，老师吹响下一组哨，学生跃入水中。'] }
];

function h3For(s) {
  const cutCount = Math.min(6, s.beats[1]-s.beats[0]+1);
  const seconds = 15 / cutCount;
  const shotList = s.shots.slice(0, cutCount);
  const aligns = shotList.map((_, i) => `图片${i+1}（来自第${i+1}镜）对齐目标视频的 ${(i*seconds).toFixed(2)} 秒处`).join('；');
  const shotLines = shotList.map((x, i) => {
    const start = (i*seconds).toFixed(3).padStart(6,'0');
    const dialog = s.dialogue[i] ? ` 说话人以对应声线说：<d>[Chinese] ${s.dialogue[i]}</d>` : '';
    return `[Shot ${i+1}] 在 ${start} 秒处，${x}，使用 ${['Static Shot','Tracking Shot','Push In','Pan Right','Close-up','Pull Out','Static Shot'][i]}，保持人物位置与泳道方向连续。${dialog}`;
  }).join('\n');
  return [
    `How the reference pictures align with the target video — ${aligns}。`,
    `subject_definitions: <Subject 1> 安娜：冷静、无感的高中女生，泳池中穿深蓝连体泳衣与白色运动外套；<Subject 2> 李想：短黑发、运动员体型、深蓝泳帽和泳镜；<Subject 3> 体育老师：成年女性体育教师，专业运动服，手持哨子与记录板；<Subject 4> 普通学生群：不复刻主角脸。`,
    `summary: ${s.setting}本段只推进游泳课事件，不增加安娜主动融入的情绪。`,
    `retention_analysis: 继承上一镜的空间朝向、人物服装、泳道编号、光照与水面状态；只继承动作连续性，不继承上一段未出现的人物和道具。`,
    `detailed_description: 16:9横屏，2K级高清，高精度日漫电影感，手绘动画背景，${shotLines}`,
    `overall_soundscape: 室内或校门环境声随场景变化；泳池段保留水面、脚步、泳道分道线轻响、哨声和学生低声反应；对白清晰，口型与台词同步。`,
    `non_diegetic_music: 无BGM，保留自然环境声与动作声。`,
    `negativePrompt: ${commonNegative}`
  ].join('\n\n');
}

const story = {source:'红绳', style:'high-precision anime cel animation', promptLang:'zh', params:{maxSegmentSeconds:15,minCutSeconds:2.5,maxCutSeconds:2.5,maxOnScreen:3,tolerance:0.15}, episodes:[{ep:3, segments:[]}]} ;

for (const s of segments) {
  const beatCount = s.beats[1]-s.beats[0]+1;
  const cutCount = Math.min(6, beatCount);
  const lengths = Array(cutCount).fill(Math.floor(beatCount/cutCount));
  for (let i=0;i<beatCount%cutCount;i++) lengths[i]++;
  let cursor=s.beats[0];
  const cuts = s.shots.slice(0,cutCount).map((frame, i) => {
    const a=cursor; const b=cursor+lengths[i]-1; cursor=b+1;
    return {beats:[a,b],seconds:15/cutCount,size:['wide','medium','close','medium','close','wide'][i],camera:['Static Shot','Tracking Shot','Push In','Pan Right','Close-up','Pull Out'][i],characters:s.chars,props:s.props,frame:`${frame}；高精度日漫电影感，cinematic anime film still，16:9横屏。`,note:'对应视频段内第'+(i+1)+'镜；该段故事板仍统一输出六宫格。'};
  });
  const rec = {...s, cuts, h3Prompt:h3For(s), durationSeconds:15, externalReferenceMapping:s.refs};
  story.episodes[0].segments.push(rec);
  const n = s.id.slice(-2);
  const segDir = path.join(active, `红绳片段${n}`);
  fs.mkdirSync(segDir,{recursive:true});
  fs.writeFileSync(path.join(segDir,'剧本定位.md'), `# ${s.id} ${s.title}\n\n- 正式剧本：../../../../02-manuscript/screenplays/红绳_第03集_泳池里的一点.md\n- 场次：S${String(s.sceneIndex).padStart(2,'0')}\n- 节拍：第${s.beats[0]}–${s.beats[1]}拍\n- 时长：15秒\n- 人物状态：安娜保持冷静、无感，不主动融入，只接受一次尝试。\n`,'utf8');
  fs.writeFileSync(path.join(segDir,'素材清单.md'), `# ${s.id} 素材清单\n\n## 参考图\n${s.refs.map((r,i)=>`- 图片${i+1}：\`${r}\``).join('\n')}\n\n## 用途\n- 六宫格故事板：构图锚点，不作为视频素材直接上传。\n- 视频参考图：按 H3 提示词中的 Picture 顺序使用。\n- 固定规则：16:9横屏、无字幕、无BGM、无水印；起跳台必须正对泳道。\n`,'utf8');
  fs.writeFileSync(path.join(segDir,'视频提示词.md'), `# ${s.id} MiniMax H3 视频提示词\n\n${rec.h3Prompt}\n`,'utf8');
  fs.writeFileSync(path.join(segDir,'故事板提示词.md'), `# ${s.id} 六宫格故事板提示词\n\n16:9横屏，1920×1080，2×3六宫格，六格按时间顺序表现同一段15秒视频的六个关键瞬间；${s.setting}；人物严格参考：${s.refs.join('、')}；每格只表现对应动作，保持人物服装、泳道方向和空间连续；高精度日漫电影感，赛璐璐人物，手绘动画背景；禁止字幕、画面文字、气泡、水印、Logo；${s.id.includes('03-06')||s.id.includes('03-07')||s.id.includes('03-08')?'起跳台必须位于泳道正前端并正对泳道，水里无人时保持空水面；':''}\n\n六格内容：\n${s.shots.map((x,i)=>`${i+1}. ${x}`).join('\n')}\n`,'utf8');
  fs.mkdirSync(path.join(out,s.id),{recursive:true});
  fs.writeFileSync(path.join(out,s.id,'prompt.md'), rec.h3Prompt+'\n','utf8');
}

fs.writeFileSync(path.join(out,'红绳_EP03-storyboard.json'), JSON.stringify(story,null,2),'utf8');
const md = ['# 《红绳》第3集 分镜与H3提示词','',`共${segments.length}段，每段15秒；每段6镜，每镜2.5秒；故事板统一六宫格。`,''];
for (const s of story.episodes[0].segments) { md.push(`## ${s.id}｜${s.title}`,`- 场次：S${String(s.sceneIndex).padStart(2,'0')}｜节拍：${s.beats[0]}–${s.beats[1]}`,`- 参考图：${s.externalReferenceMapping.join('、')}`,'',s.h3Prompt,'', '---',''); }
fs.writeFileSync(path.join(out,'红绳_EP03-storyboard.md'), md.join('\n'),'utf8');
fs.writeFileSync(path.join(out,'manifest.json'), JSON.stringify({source:'红绳',episode:3,segments:segments.map(s=>({id:s.id,title:s.title,folder:s.id,frames:'故事板.png',prompt:'prompt.md'}))},null,2),'utf8');
console.log(`built ${segments.length} segments`);

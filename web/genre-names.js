// Display-only translations and editorial reading aids, never identifiers.
// Descriptive labels are not official definitions of the Every Noise taxonomy.

const terms = Object.fromEntries(`
pop|流行
music|音乐
deep|深度
new|新式
old school|老派
old-school|老派
school|派
hard|硬派
soft|柔和
darkwave|暗潮
coldwave|冷潮
post-grunge|后垃圾摇滚
nu metal|新金属
art pop|艺术流行
art rock|艺术摇滚
album rock|专辑摇滚
heartland rock|美国腹地摇滚
garage rock|车库摇滚
garage punk|车库朋克
garage|车库
glam rock|华丽摇滚
glam metal|华丽金属
yacht rock|游艇摇滚
roots rock|根源摇滚
roots|根源
southern rock|南方摇滚
southern|南方
southern hip hop|美国南部嘻哈
east coast hip hop|美国东海岸嘻哈
west coast rap|美国西海岸说唱
gangster rap|匪帮说唱
conscious hip hop|意识嘻哈
conscious|意识
cloud rap|云说唱
bedroom pop|卧室流行
bedroom|卧室
slap house|Slap 浩室
big room|大房间电子舞曲
electro house|电子浩室
future bass|未来贝斯
bass music|低音电子音乐
bass|贝斯
drum|鼓
drums|鼓
breaks|碎拍
hard bop|硬波普爵士
bop|波普爵士
cool jazz|冷爵士
free improvisation|自由即兴
improvisation|即兴
free|自由
spoken word|口语表演
poetry|诗歌
field recording|田野录音
field recordings|田野录音
sound art|声音艺术
sound collage|声音拼贴
musique concrete|具体音乐
drone|持续音
noise rock|噪音摇滚
noise pop|噪音流行
noise punk|噪音朋克
easy listening|轻音乐
adult standards|成人经典流行
adult pop|成人流行
adult contemporary|成人当代流行
urban contemporary|都市当代音乐
pop rock|流行摇滚
pop rap|流行说唱
dance pop|舞曲流行
chamber pop|室内流行
baroque pop|巴洛克流行
europop|欧洲流行
eurodance|欧洲舞曲
eurobeat|欧陆节拍
eurodisco|欧洲迪斯科
italo disco|意大利迪斯科
italo dance|意式舞曲
euro|欧洲
indietronica|独立电子
folktronica|民谣电子
hyperpop|超流行
glitch|故障电子
glitch hop|故障嘻哈
k-pop|韩国流行
j-pop|日本流行
j-rock|日本摇滚
c-pop|华语流行
mandopop|国语流行
cantopop|粤语流行
k-pop boy group|韩国流行男团
k-pop girl group|韩国流行女团
boy band|男子组合
girl group|女子组合
opm|菲律宾原创流行
ccm|当代基督教音乐
urbano latino|拉丁都市音乐
trap latino|拉丁 Trap 音乐
urbano espanol|西班牙都市音乐
rock en espanol|西班牙语摇滚
pop urbaine|法语都市流行
rap francais|法国说唱
musica mexicana|墨西哥音乐
musica popular brasileira|巴西流行音乐
mpb|巴西流行音乐
funk carioca|里约放克舞曲
baile funk|巴西放克舞曲
pagode|帕戈德桑巴
forro|弗罗舞曲
sertanejo|巴西乡村
sertanejo universitario|巴西大学乡村
sertanejo pop|巴西乡村流行
arrocha|阿罗恰舞曲
agronejo|巴西农业乡村流行
corrido|墨西哥叙事民谣
corridos tumbados|新派墨西哥叙事民谣
norteno|墨西哥北方音乐
sierreno|墨西哥山地音乐
sad sierreno|忧伤墨西哥山地音乐
ranchera|墨西哥牧场歌曲
banda|墨西哥班达管乐
grupera|墨西哥乐队流行
filmi|印度电影音乐
bollywood|宝莱坞电影音乐
desi|南亚
bhangra|邦格拉舞曲
qawwali|卡瓦利苏菲颂唱
ghazal|加扎勒歌曲
carnatic|卡纳提克古典音乐
hindustani|印度斯坦古典音乐
enka|演歌
kayokyoku|日本歌谣曲
city pop|城市流行
vocaloid|虚拟歌手音乐
anime rock|动画摇滚
anime score|动画配乐
otacore|御宅文化音乐
visual kei|视觉系
shibuya-kei|涩谷系
chanson|法语香颂
schlager|德语通俗歌谣
hoerspiel|广播剧
polka|波尔卡
waltz|华尔兹
marching band|行进乐队
brass band|铜管乐团
concert band|管乐团
wind ensemble|管乐合奏
military band|军乐队
band|乐队
ballad|抒情歌曲
ballroom|交谊舞音乐
sea shanties|海员号子
workout|健身
fitness|健身
yoga|瑜伽
therapy|疗愈
background|背景
rain|雨声
nature|自然声音
white noise|白噪音
ocean|海洋声音
birdsong|鸟鸣
asmr|ASMR 自主感官经络反应
lo-fi beats|低保真节拍
beats|节拍
beat|节拍
sped up|加速版
slowed and reverb|降速混响
remixes|混音
rock|摇滚
hip hop|嘻哈
rap|说唱
jazz|爵士
blues|布鲁斯
folk|民谣
country|乡村
classical|古典
electronic|电子
electronica|电子音乐
metal|金属
punk|朋克
soul|灵魂乐
funk|放克
disco|迪斯科
reggae|雷鬼
ska|斯卡
gospel|福音
ambient|氛围
new age|新世纪音乐
synthpop|合成器流行
synthwave|合成器波
electropop|电子流行
electro|电子
electro swing|电子摇摆
new wave|新浪潮
post-punk|后朋克
post-rock|后摇滚
post-metal|后金属
hard rock|硬摇滚
soft rock|软摇滚
heavy metal|重金属
black metal|黑金属
death metal|死亡金属
doom metal|厄运金属
power metal|力量金属
thrash metal|鞭挞金属
speed metal|速度金属
metalcore|金属核
deathcore|死核
grindcore|碾核
hardcore|硬核
shoegaze|自赏摇滚
dream pop|梦幻流行
grunge|垃圾摇滚
emo|情绪摇滚
emo rap|情绪说唱
math rock|数学摇滚
indie|独立
alternative|另类
experimental|实验
progressive|前卫
psychedelic|迷幻
acoustic|原声
instrumental|器乐
vocal|人声
traditional|传统音乐
contemporary|当代
modern|现代
classic|经典
vintage|复古
retro|复古
melodic|旋律
symphonic|交响
orchestral|管弦
baroque|巴洛克
romantic|浪漫主义
romanticism|浪漫主义
minimal|极简
minimalism|极简主义
avant-garde|先锋
underground|地下
christian|基督教
worship|敬拜
medieval|中世纪
renaissance|文艺复兴
opera|歌剧
operatic pop|歌剧跨界流行
chamber music|室内乐
chamber ensemble|室内乐团
choir|合唱
choral|合唱
a cappella|无伴奏合唱
orchestra|管弦乐团
youth orchestra|青年管弦乐团
singer-songwriter|创作歌手
piano|钢琴
guitar|吉他
violin|小提琴
cello|大提琴
viola|中提琴
flute|长笛
saxophone|萨克斯
trumpet|小号
clarinet|单簧管
oboe|双簧管
bassoon|巴松管
harp|竖琴
organ|管风琴
percussion|打击乐
strings|弦乐
brass|铜管
accordion|手风琴
harmonica|口琴
banjo|班卓琴
ukulele|尤克里里
mandolin|曼陀林
bagpipe|风笛
string quartet|弦乐四重奏
solo|独奏
duo|二重奏
trio|三重奏
quartet|四重奏
quintet|五重奏
ensemble|合奏
performance|演奏
soundtrack|配乐
score|影视配乐
video game music|电子游戏音乐
anime|动画
comedy|喜剧
children's music|儿童音乐
children|儿童
kids|儿童
lullaby|摇篮曲
sleep|睡眠背景音乐
meditation|冥想
relaxation|放松
christmas|圣诞
holiday|节庆
world|世界
afrobeat|非洲节拍
afrobeats|非洲流行节拍
afropop|非洲流行
afro house|非洲浩室
bossa nova|波萨诺瓦
samba|桑巴
salsa|萨尔萨
tango|探戈
flamenco|弗拉门戈
fado|法朵
reggaeton|雷鬼顿
bachata|巴恰塔舞曲
merengue|梅伦格舞曲
cumbia|昆比亚
bolero|波莱罗情歌
rumba|伦巴
kizomba|基宗巴
urban kiz|Urban Kiz 舞曲
house|浩室
deep house|深度浩室
tech house|科技浩室
progressive house|前卫浩室
tropical house|热带浩室
future house|未来浩室
acid house|酸性浩室
techno|Techno 电子舞曲
trance|出神舞曲
psytrance|迷幻出神舞曲
drum and bass|鼓打贝斯
drumfunk|鼓放克
jungle|丛林舞曲
dubstep|Dubstep 低音舞曲
dub|Dub 混音
grime|Grime 音乐
instrumental grime|Grime 器乐
drill|Drill 说唱
trap|Trap 音乐
phonk|孟菲斯说唱衍生电子音乐
edm|电子舞曲
dance|舞曲
dancehall|舞厅雷鬼
breakbeat|碎拍
broken beat|碎拍音乐
breakcore|碎核
hardstyle|硬派舞曲
gabber|加巴硬核
happy hardcore|欢乐硬核
trip hop|神游舞曲
downtempo|慢拍电子
chillout|驰放
chill|舒缓
chillwave|寒潮
vaporwave|蒸汽波
lo-fi|低保真
noise|噪音
industrial|工业
dark|暗黑
gothic|哥特
goth|哥特
ebm|电子身体音乐
idm|智能舞曲
8-bit|八位电子
chiptune|芯片音乐
remix|混音
cover|翻唱
tribute|致敬
big band|大乐队爵士
swing|摇摆爵士
bebop|比博普爵士
free jazz|自由爵士
smooth jazz|流畅爵士
jazz fusion|融合爵士
fusion|融合
r&b|节奏布鲁斯
neo soul|新灵魂乐
bluegrass|蓝草
americana|美式根源音乐
celtic|凯尔特
musica eletronica brasileira|巴西电子音乐
afro house angolano|安哥拉非洲浩室
chill baile|舒缓巴西放克舞曲
new french touch|新法式电子舞曲
french touch|法式电子舞曲
popwave|流行合成器波
aussietronica|澳大利亚电子音乐
viet edm|越南电子舞曲
turkce remix|土耳其语混音
solipsynthm|Solipsynthm 合成器电子音乐
folk-pop|民谣流行
post-hardcore|后硬核
post-bop|后波普爵士
post-minimalism|后极简主义
post-disco|后迪斯科
post-screamo|后尖叫情绪核
neo-classical|新古典
neoclassicism|新古典主义
neo-psychedelic|新迷幻
neo-psychedelia|新迷幻音乐
neo-synthpop|新合成器流行
neo-singer-songwriter|新派唱作人
neo r&b|新派节奏布鲁斯
neo-traditional|新传统
neo-trad|新传统
proto-metal|原始金属
protopunk|原始朋克
proto-rap|早期说唱
proto-hyperpop|早期超流行
power pop|强力流行
power-pop|强力流行
power noise|强噪音
power electronics|强力电子噪音
groove metal|律动金属
stoner rock|迷幻硬摇滚
stoner metal|迷幻金属
stoner|迷幻重型
sludge metal|泥浆金属
sludgecore|泥浆硬核
sludge|泥浆
thrash-groove metal|鞭击律动金属
thrash|鞭击金属
technical death metal|技术死亡金属
brutal death metal|残酷死亡金属
melodeath|旋律死亡金属
death doom|死亡厄运金属
funeral doom|葬礼厄运金属
doom|厄运金属
blackened|黑金属化
atmospheric|氛围
technical|技术型
epic|史诗
occult|神秘学主题
raw|原始粗粝
war metal|战争金属
viking metal|维京金属
fantasy metal|奇幻主题金属
tolkien metal|托尔金主题金属
lovecraftian metal|洛夫克拉夫特主题金属
forest black metal|森林主题黑金属
nwobhm|英国重金属新浪潮
unblack metal|基督教黑金属
djent|切分重音前卫金属
shred|速弹吉他
prog|前卫
psych|迷幻
heavy psych|重型迷幻摇滚
psychedelia|迷幻音乐
rock-and-roll|摇滚乐
rhythm and blues|节奏布鲁斯
blues-rock|布鲁斯摇滚
rockabilly|乡村摇滚
psychobilly|迷幻乡村摇滚
britpop|英伦流行摇滚
britpop revival|英伦摇滚复兴
merseybeat|默西节拍
british invasion|英国入侵时期摇滚
madchester|曼彻斯特另类舞曲摇滚
pub rock|酒吧摇滚
swamp rock|沼泽摇滚
acid rock|酸性迷幻摇滚
jam band|即兴摇滚乐队
surf music|冲浪音乐
surf|冲浪
surf punk|冲浪朋克
skate punk|滑板朋克
horror punk|恐怖主题朋克
street punk|街头朋克
glam punk|华丽朋克
art punk|艺术朋克
punk 'n' roll|朋克摇滚融合
oi|街头朋克
riot grrrl|女性主义朋克
no wave|无浪潮
harsh noise wall|极端噪音音墙
screamo|尖叫情绪核
slowcore|慢核
mathcore|数学核
deathgrind|死亡碾核
cybergrind|电子碾核
mathgrind|数学碾核
necrogrind|恐怖主题碾核
mincecore|原始粗粝碾核
noisecore|噪音核
emocore|情绪硬核
emoviolence|极端情绪硬核
easycore|流行朋克与硬核融合
electronicore|电子核
nintendocore|电玩电子硬核
trancecore|迷幻舞曲与硬核融合
digital hardcore|数字硬核
nu-metalcore|新金属核
screamocore|尖叫情绪核融合
swancore|繁复吉他后硬核
post-teen pop|青年流行
teen pop|青少年流行
bubblegum pop|泡泡糖流行
bubblegum dance|泡泡糖舞曲
sunshine pop|阳光流行
sophisti-pop|精致流行
jangle pop|清亮吉他流行
jangle rock|清亮吉他摇滚
hypnagogic pop|朦胧复古流行
indiecoustica|原声独立音乐
indie poptimism|明快独立流行
indie anthem-folk|合唱式独立民谣
anti-folk|反民谣
outlaw country|叛道乡村
honky tonk|酒馆乡村
honky-tonk|酒馆乡村
western swing|西部摇摆
country road|乡村音乐听感分支
country dawn|乡村音乐听感分支
red dirt|红土乡村
countrygaze|乡村与盯鞋融合
jamgrass|即兴蓝草
deathgrass|重型蓝草融合
tex-mex|得克萨斯墨西哥融合音乐
tejano|得州墨西哥裔音乐
nashville sound|纳什维尔乡村之声
bakersfield sound|贝克斯菲尔德乡村之声
bluegrass fiddle|蓝草小提琴
old-time|美国旧时民间音乐
appalachian|阿巴拉契亚
protest folk|抗议民谣
shanty|水手号子
sean-nos singing|爱尔兰无伴奏传统歌唱
motown|摩城灵魂乐
quiet storm|柔情节奏布鲁斯
northern soul|北方灵魂乐
memphis soul|孟菲斯灵魂乐
philly soul|费城灵魂乐
doo-wop|嘟哇和声
new jack swing|新杰克摇摆
torch song|伤感情歌
minneapolis sound|明尼阿波利斯放克之声
p funk|迷幻放克
g funk|西海岸放克说唱
boom bap|重鼓点老派嘻哈
hip pop|嘻哈流行融合
hip house|嘻哈浩室
hip-hop|嘻哈
hip-hop experimental|实验嘻哈
abstract hip hop|抽象嘻哈
political hip hop|政治主题嘻哈
golden age hip hop|黄金年代嘻哈
dirty south rap|美国南部说唱
gangsta rap|匪帮说唱
battle rap|对战说唱
conscious rap|意识说唱
rage rap|躁动电子说唱
sad rap|伤感说唱
meme rap|网络梗说唱
scream rap|嘶吼说唱
scam rap|诈骗叙事说唱
chicano rap|墨西哥裔美国说唱
plugg|柔和合成器陷阱说唱
plug|柔和合成器陷阱说唱
pluggnb|柔和陷阱节拍与节奏布鲁斯融合
emoplugg|情绪化柔和陷阱说唱
dream plugg|梦幻柔和陷阱说唱
dark plugg|暗黑柔和陷阱说唱
drift phonk|漂移风电子说唱
gym phonk|健身向电子说唱
aggressive phonk|强烈电子说唱
hyphy|旧金山湾区派对嘻哈
crunk|南部派对嘻哈
bboy|霹雳舞音乐
popping|震感舞音乐
freestyle|自由式音乐
brostep|重低音爆裂回响贝斯
complextro|繁复音色电子浩室
big beat|大节拍电子
new rave|新锐舞
rave|锐舞
acid|酸性
intelligent dance music|实验性电子舞曲
braindance|实验电子舞曲
wonky|错位节奏电子音乐
future garage|未来车库电子
microhouse|微型浩室
filter house|滤波浩室
tribal house|部落节奏浩室
organic house|自然音色浩室
float house|漂浮感浩室
diva house|女声浩室
funky house|放克浩室
bouncy house|弹跳节奏浩室
stutter house|切碎重复人声浩室
g-house|匪帮说唱浩室
nu disco|新迪斯科
nu jazz|新爵士融合
jazztronica|爵士电子融合
chillhop|舒缓嘻哈
jazzhop|爵士嘻哈
jazzcore|爵士硬核融合
livetronica|现场演奏电子音乐
funktronica|放克电子
latintronica|拉丁电子
ethnotronica|民族电子融合
electroclash|复古电子碰撞
electropowerpop|强力电子流行
electro-pop|电子流行
electro-industrial|电子工业
dark wave|暗潮
ethereal wave|空灵暗潮
neoclassical darkwave|新古典暗潮
futurepop|未来流行电子
dark cabaret|暗黑歌舞音乐
darksynth|暗黑合成器音乐
chillsynth|舒缓合成器音乐
comfy synth|温馨合成器音乐
minimal synth|极简合成器音乐
keller synth|地下粗粝合成器音乐
hardwave|强劲波系电子音乐
hardvapour|粗粝蒸汽电子
witch house|女巫浩室
dreampunk|梦幻氛围电子
grungegaze|垃圾摇滚与盯鞋融合
nu gaze|新盯鞋
sinogaze|华语盯鞋
italogaze|意大利盯鞋
bitpop|芯片流行
chip hop|芯片嘻哈
vapor soul|电子灵魂乐分支
vapor pop|电子流行分支
vapor twitch|网络电子音乐分支
vapor house|蒸汽浩室
illbient|实验氛围嘻哈
glitchcore|故障电子核
glitchbreak|故障碎拍
neurofunk|神经放克鼓打贝斯
liquid funk|流畅放克鼓打贝斯
dancefloor dnb|舞池鼓打贝斯
jump up|跳跃型鼓打贝斯
ragga jungle|雷鬼丛林电子
bassline|低音线舞曲
uk funky|英国放克电子舞曲
ukg revival|英国车库复兴
jersey club|泽西俱乐部舞曲
baltimore club|巴尔的摩俱乐部舞曲
bmore|巴尔的摩俱乐部舞曲
miami bass|迈阿密低音舞曲
afroswing|非洲节奏与英国说唱融合
amapiano|南非钢琴浩室
kwaito|南非城镇舞曲
gqom|南非极简鼓点舞曲
azonto|加纳阿宗托舞曲
azontobeats|加纳阿宗托节奏
moombahton|慢速浩室与雷鬼顿融合
rawstyle|粗粝硬派舞曲
euphoric hardstyle|激昂旋律硬派舞曲
uptempo hardcore|超快节奏硬核电子
speedcore|极速硬核电子
terrorcore|极端硬核电子
extratone|超高速音墙电子
flashcore|极速实验电子
doomcore|缓慢暗黑硬核电子
frenchcore|法国硬核电子
tekk|快节奏硬派电子
jumptek|跳跃硬派电子
hi-nrg|高能量舞曲
hi-tech|高速迷幻电子
psytech|迷幻科技舞曲
psybreaks|迷幻碎拍
goa trance|果阿迷幻舞曲
full on|强劲旋律迷幻舞曲
darkpsy|暗黑迷幻舞曲
uplifting trance|振奋旋律迷幻舞曲
hypertrance|高能迷幻舞曲
hands up|举手派电子舞曲
nightcore|加速升调电子音乐
deconstructed club|解构俱乐部音乐
algorave|算法生成锐舞
electroacoustic|电声
electroacoustic composition|电声作曲
acousmatic|听觉具象电声音乐
xenharmonic|非传统音律音乐
microtonal|微分音
totalism|整体主义实验音乐
impressionism|印象主义音乐
classical era|古典主义时期音乐
early music|早期古典音乐
early romantic era|早期浪漫主义音乐
late romantic era|晚期浪漫主义音乐
post-romantic era|后浪漫主义音乐
early modern classical|早期现代古典音乐
historically informed performance|历史知情演奏
historic|历史录音
historical keyboard|历史键盘乐器
string orchestra|弦乐团
pops orchestra|通俗管弦乐
radio symphony|广播交响乐团
wind symphony|管乐交响
wind quintet|木管五重奏
string quintet|弦乐五重奏
string trio|弦乐三重奏
chamber choir|室内合唱
cathedral choir|教堂合唱
university choir|大学合唱
women's choir|女声合唱
men's choir|男声合唱
boy soprano|男童高音
soprano|女高音
mezzo-soprano|女中音
contralto|女低音
tenor|男高音
countertenor|假声男高音
baritone|男中音
opera chorus|歌剧合唱
art song|艺术歌曲
lied|艺术歌曲
oratory|清唱剧
gregorian chant|格里高利圣咏
chant|吟诵
byzantine|拜占庭圣咏
ars subtilior|精微艺术时期音乐
trecento|意大利十四世纪音乐
minnesang|德国中世纪爱情歌
troubadour|中世纪游吟诗人音乐
trouvere|法国北部中世纪游吟诗人音乐
prepared piano|预置钢琴
honky-tonk piano|酒馆风格钢琴
barrelhouse piano|粗犷酒馆布鲁斯钢琴
fingerstyle|指弹吉他
steel guitar|钢棒吉他
pedal steel guitar|踏板钢棒吉他
viola da gamba|维奥尔琴
lute|鲁特琴
recorder|竖笛
theremin|特雷门电子琴
akordeon|手风琴
harmonikka|手风琴
fisarmonica|手风琴
concertina|六角手风琴
organetto|意大利小手风琴
bandolim|曼陀林
clawhammer banjo|击弦班卓琴
autoharp|自动竖琴
zither|齐特琴
hammered dulcimer|扬琴
mountain dulcimer|阿巴拉契亚扬琴
fiddle|民间小提琴
nyckelharpa|瑞典键控提琴
hardingfele|挪威哈当厄尔提琴
hurdy-gurdy|轮擦提琴
uilleann pipes|爱尔兰肘风笛
scottish smallpipe|苏格兰小风笛
alphorn|阿尔卑斯长号
euphonium|上低音号
woodwind|木管
mallet|槌击乐器
handpan|手碟
steelpan|钢鼓
marimba|马林巴琴
balafon|西非木琴
guzheng|古筝
guqin|古琴
pipa|琵琶
huqin|胡琴
dizi|笛子
shakuhachi|尺八
koto|日本筝
gayageum|伽倻琴
taiko|日本太鼓
gong|锣
tabla|塔布拉鼓
sarangi|萨朗吉琴
sarod|萨罗德琴
veena|维纳琴
santoor|桑图尔扬琴
santur|桑图尔扬琴
shehnai|印度唢呐
nadaswaram|南印度双簧管
duduk|亚美尼亚杜杜克笛
baglama|土耳其巴格拉玛琴
qanun|中东卡农琴
ngoni|西非恩戈尼琴
kora|西非科拉琴
djembe|西非金贝鼓
darbuka|中东杯鼓
balalaika|俄罗斯三角琴
dombra|冬不拉
bandura|乌克兰班杜拉琴
gaita|伊比利亚风笛
violao|巴西原声吉他
music box|音乐盒
handbells|手铃
bells|钟铃音乐
ost|影视原声
vgm|电子游戏音乐
bgm|背景音乐
movie tunes|电影歌曲
show tunes|音乐剧歌曲
broadway|百老汇音乐剧
west end|伦敦西区音乐剧
hollywood|好莱坞影视音乐
rhythm game|音游音乐
anime game|动漫游戏音乐
idol game|偶像游戏音乐
idol|偶像音乐
idol pop|偶像流行
idol rock|偶像摇滚
boy group|男子组合
vtuber|虚拟主播音乐
anime cv|动漫声优歌曲
seiyu|声优歌曲
denpa-kei|电波系歌曲
idol kayo|日本偶像歌谣
ryukoka|日本流行歌谣
min'yo|日本民谣
trot|韩国传统流行歌谣
dong-yo|韩国儿歌
xinyao|新加坡新谣
zhongguo feng|中国风
hakkapop|客家流行
hong kong tv drama|香港电视剧音乐
chinese new year|华人贺岁音乐
taiwan graduation song|台湾毕业歌曲
fo jing|佛经吟诵
quran|古兰经诵读
islamic recitation|伊斯兰经文吟诵
nasheed|伊斯兰赞歌
nasyid|伊斯兰赞歌
sufi|苏菲音乐
sufi chant|苏菲吟诵
mevlevi sufi|梅夫拉维苏菲音乐
bhajan|印度宗教赞歌
kirtan|印度应答式赞歌
mantra|真言吟诵
shabad|锡克教圣歌
hare krishna|克里希纳颂唱
sholawat|伊斯兰赞圣歌
gregorian dance|圣咏融合舞曲
shamanic|萨满仪式音乐
native american spiritual|美洲原住民灵性音乐
healing|舒缓疗愈主题音乐
healing hz|疗愈主题音频（非疗效承诺）
solfeggio product|疗愈频率主题音频（非疗效承诺）
focus|专注背景音乐
study beats|学习伴奏节拍
focus beats|专注背景节拍
lo-fi study|学习用低保真音乐
brain waves|脑波主题背景音
binaural|双耳音频
8d|环绕移动声像音频
pink noise|粉红噪音
color noise|彩色噪音
environmental|环境声音
water|水声
whale song|鲸歌
pet calming|宠物安抚背景音
massage|按摩背景音乐
mindfulness|正念背景音乐
hypnosis|催眠背景音
relaxative|放松背景音乐
reading|阅读背景音乐
writing|写作背景音乐
workout product|健身配乐
pilates|普拉提配乐
gaming edm|游戏向电子舞曲
gaming dubstep|游戏向回响贝斯
game mood|游戏氛围音乐
ballet class|芭蕾训练配乐
wrestling|摔角节目音乐
birthday|生日歌曲
halloween|万圣节主题音乐
ringtone|手机铃声
parody|戏仿音乐
novelty|趣味歌曲
meme|网络梗音乐
comic|喜剧音乐
cartoon|动画音乐
drama|戏剧音乐
prank|恶作剧音频
sound|声音类音频
theme|主题音乐
backing track|伴奏音轨
children's folk|儿童民谣
nursery|幼儿歌谣
preschool children's music|学龄前儿童音乐
kindermusik|儿童音乐
musica infantil|儿童音乐
musica para ninos|儿童音乐
musica per bambini|儿童音乐
musique pour enfants|儿童音乐
muziek voor kinderen|儿童音乐
barnmusik|儿童音乐
barnemusikk|儿童音乐
cocuk sarkilari|儿童歌曲
kinderliedjies|儿童歌曲
lastelaulud|儿童歌曲
dytyachi pisni|儿童歌曲
djecje pjesme|儿童歌曲
decije pesme|儿童歌曲
bernu dziesmas|儿童歌曲
otroske pesmice|儿童歌曲
nhac thieu nhi|越南儿童歌曲
haur kantak|巴斯克儿童歌曲
kleine hoerspiel|儿童广播剧
barnsagor|儿童故事音频
cocuk masallari|儿童童话音频
detskie rasskazy|儿童故事音频
lasten satuja|儿童童话音频
rozpravky|童话音频
pohadky|童话音频
hangoskonyvek|有声读物
lesen|朗读音频
talent show|选秀节目音乐
talentschau|选秀节目音乐
talentkonkurrence|选秀节目音乐
talentos brasileiros|巴西选秀音乐
viral|网络热门
viral pop|网络热门流行
viral rap|网络热门说唱
social media pop|社交媒体流行
women's music|女性音乐创作
lgbtq+|性少数群体
transpop|跨性别音乐人流行
gay chorus|性少数群体合唱
sad|伤感
melancholia|忧郁氛围音乐
calming|舒缓
abstract|抽象实验
organic|自然音色
compositional ambient|作曲式氛围音乐
drumless|弱鼓点
metallic|金属化
chaotic|混乱型
revival|复兴
diy|自助制作
supergroup|明星联合乐队
new wave of speed metal|新一代速度金属
permanent wave|跨年代另类摇滚
mellow gold|柔和经典流行摇滚
stomp and holler|强节拍合唱式民谣
stomp and flutter|轻快节拍民谣分支
stomp pop|强节拍流行
alt z|新式另类流行
pov: indie|网络独立音乐标签
escape room|实验电子与流行融合
metropopolis|都市电子流行
neo mellow|柔和当代流行
shimmer pop|明亮电子流行
shiver pop|独立流行细分标签
etherpop|空灵流行
gauze pop|朦胧流行
candy pop|甜美流行
pixie|流行朋克相关分支
small room|小众独立音乐
scorecore|影视配乐相关音乐
epicore|史诗配乐相关音乐
hopebeat|明快励志流行
gymcore|健身向重型音乐
lowercase|微弱声音实验音乐
lounge|休闲沙发音乐
dinner jazz|用餐背景爵士
hot jazz|早期热爵士
dixieland|迪克西兰爵士
gypsy jazz|吉普赛爵士
ecm-style jazz|ECM 唱片风格爵士
klezmer|犹太克莱兹默民间音乐
cajun|卡津民间音乐
zydeco|路易斯安那克里奥尔舞曲
praise|赞美诗歌
classic praise|经典赞美诗歌
louvor|葡语赞美诗歌
adoracao|葡语敬拜音乐
liedermacher|德语民谣唱作
cantautor|西语唱作人音乐
cantautora|西语女唱作人音乐
canzone d'autore|意大利唱作人音乐
variete francaise|法国通俗歌曲
nouvelle chanson francaise|法国新香颂
ye ye|耶耶流行
iskelma|芬兰通俗歌谣
levenslied|荷兰生活歌谣
volksmusik|德语地区民间音乐
volkstumliche musik|德语民间风格通俗音乐
volkspop|民间流行融合
partyschlager|派对通俗歌谣
dansband|北欧舞厅乐队音乐
dansktop|丹麦通俗歌谣
disco polo|波兰迪斯科
discofox|迪斯科狐步舞曲
neue deutsche welle|德国新浪潮
neue neue deutsche welle|新一代德国新浪潮
neue deutsche harte|德国新硬派工业金属
deutschrock|德语摇滚
nederpop|荷兰流行
nederreggae|荷兰雷鬼
musica|音乐
musique|音乐
eletronica|电子音乐
rock nacional|本土摇滚
pop nacional|本土流行
musica de fondo|背景音乐
romantico|浪漫抒情
triste|伤感
cristiano|基督教
cristao|基督教
cristiana|基督教
electronico|电子
alternativo|另类
clasicos|经典
tradicional|传统
antigas|老歌
antigo|早期
consciente|社会意识主题
conscient|社会意识主题
conciencia|社会意识主题
politico|政治主题
calme|舒缓
urbano|都市音乐
reggaeton flow|雷鬼顿节奏
perreo|雷鬼顿舞曲
neoperreo|新雷鬼顿舞曲
dembow|登波舞曲
reggae en espanol|西班牙语雷鬼
reggae do maranhao|巴西马拉尼昂雷鬼
lovers rock|柔情雷鬼
rocksteady|稳拍雷鬼
soca|索卡舞曲
mento|牙买加曼托民间音乐
nyahbinghi|拉斯塔法里鼓乐
zouk|祖克舞曲
zouk riddim|祖克节奏
kompa|海地孔帕舞曲
mambo|曼波舞曲
timba|古巴廷巴舞曲
son cubano|古巴颂乐
trova|拉丁吟唱歌曲
nueva cancion|拉丁美洲新歌运动
vallenato|哥伦比亚瓦耶纳托
cuarteto|阿根廷库阿尔特托舞曲
cumbia sonidera|音响派对坎比亚
cumbia villera|阿根廷城郊坎比亚
cumbia 420|都市坎比亚融合
chicha|秘鲁迷幻坎比亚
mariachi|墨西哥马里亚奇
duranguense|杜兰戈舞曲
tecnobanda|电子班达舞曲
norteno-sax|萨克斯北方墨西哥音乐
corridos|墨西哥叙事歌
corridos belicos|战斗叙事墨西哥歌曲
grupero|墨西哥乐队流行
gruperas inmortales|经典墨西哥乐队流行
musica popular colombiana|哥伦比亚通俗音乐
tierra caliente|墨西哥热地民间音乐
huayno|安第斯瓦伊诺民间音乐
chamame|查马梅民间舞曲
candombe|乌拉圭坎东贝鼓乐
murga|南美狂欢节歌舞
marinera|秘鲁马里内拉舞曲
son jarocho|墨西哥韦拉克鲁斯民间音乐
sertanejo tradicional|传统巴西乡村
pagode novo|新派帕戈德桑巴
samba-enredo|桑巴巡游主题歌
samba de roda|圆圈桑巴
roda de samba|围坐桑巴
samba-jazz|桑巴爵士
samba-rock|桑巴摇滚
partido alto|即兴对唱桑巴
jovem guarda|巴西青年摇滚潮流
velha guarda|老一辈桑巴
axe|巴伊亚阿谢舞曲
piseiro|巴西键盘弗罗舞曲
brega|巴西通俗情歌
brega funk|巴西情歌与放克舞曲融合
tecnobrega|巴西电子情歌舞曲
arrochadeira|巴西阿罗沙舞曲
funk mtg|巴西放克剪辑混音
funk mandelao|强低音巴西放克
funk ostentacao|炫耀主题巴西放克
funk melody|旋律巴西放克
funk 150 bpm|每分钟150拍巴西放克
tropicalia|巴西热带主义音乐
manguebeat|巴西红树林节拍
maracatu|巴西马拉卡图鼓乐
frevo|巴西弗雷沃狂欢舞曲
choro|巴西肖罗器乐
nova mpb|新巴西流行音乐
psicodelia|迷幻音乐
turbo folk|巴尔干电子民间流行
manele|罗马尼亚曼内莱流行
chalga|保加利亚民间流行
sevdah|波斯尼亚情歌
laiko|希腊通俗歌谣
entehno|希腊艺术民谣
nisiotika|希腊群岛民间音乐
arabesk|土耳其阿拉伯风流行
anadolu rock|安纳托利亚摇滚
rai|阿尔及利亚拉伊音乐
shaabi|阿拉伯通俗民间音乐
mahraganat|埃及电子街头舞曲
khaliji|海湾阿拉伯音乐
gnawa|摩洛哥格纳瓦仪式音乐
dabke|黎凡特达布卡民间舞曲
dhrupad|德鲁帕德古典声乐
mollywood|马拉雅拉姆语电影音乐
kollywood|泰米尔语电影音乐
tollywood|泰卢固语电影音乐
sandalwood|卡纳达语电影音乐
dangdut|印度尼西亚当杜特
dangdut koplo|快节奏当杜特舞曲
gamelan|甘美兰乐团
molam|泰老莫兰民间歌唱
luk thung|泰国乡村歌谣
pansori|韩国盘索里
yoik|萨米约伊克吟唱
hula|夏威夷草裙舞音乐
highlife|西非高寿音乐
benga|肯尼亚本加音乐
bongo flava|坦桑尼亚流行嘻哈
juju|尼日利亚朱朱音乐
fuji|尼日利亚富士音乐
bikutsi|喀麦隆比库齐舞曲
chimurenga|津巴布韦奇穆伦加音乐
maskandi|祖鲁马斯坎迪音乐
marrabenta|莫桑比克马拉本塔舞曲
kuduro|安哥拉库杜罗舞曲
seggae|毛里求斯塞卡与雷鬼融合
maloya|留尼汪马洛亚音乐
taarab|东非塔拉布音乐
fado de coimbra|科英布拉法朵
flamenco urbano|都市弗拉门戈
cante flamenco|弗拉门戈歌唱
zarzuela|西班牙萨苏埃拉歌剧
tarantella|意大利塔兰泰拉舞曲
skiffle|噪音爵士民间融合
zeuhl|泽尔前卫摇滚
rock in opposition|反对派摇滚
skweee|北欧合成器放克
suomisaundi|芬兰迷幻电子
fife and drum|横笛与鼓乐
string band|弦乐民间乐队
jug band|壶乐队民间音乐
military cadence|军队行进号子
police band|警察乐队
college marching band|大学行进乐队
ethnomusicology|民族音乐研究录音
alt pop|另类流行
alt-idol|另类偶像音乐
gen z singer-songwriter|Z世代唱作人
latin arena pop|拉丁体育场流行
neon pop punk|明亮流行朋克
electric blues|电声布鲁斯
delta blues|三角洲布鲁斯
piedmont blues|皮德蒙特布鲁斯
swamp blues|沼泽布鲁斯
jump blues|跳跃布鲁斯
desert blues|沙漠布鲁斯
rhythm and boogie|节奏与布吉
boogie|布吉
space rock|太空摇滚
space age pop|太空时代流行
space ambient|太空氛围
spacewave|太空电子
spacegrunge|太空感垃圾摇滚
space|太空主题
cyberpunk|赛博朋克主题音乐
steampunk|蒸汽朋克主题音乐
afrofuturism|非洲未来主义音乐
afrofuturismo brasileiro|巴西非洲未来主义音乐
afro r&b|非洲节奏布鲁斯
afro soul|非洲灵魂乐
afro drill|非洲钻头说唱
afro-funk|非洲放克
afro-cuban percussion|非洲古巴打击乐
latina|拉丁
latino|拉丁
tropical|热带拉丁音乐
folklore|民间音乐
folclore|民间音乐
folclor|民间音乐
folkmusik|北欧民间音乐
folclore portugues|葡萄牙民间音乐
traditionalista|传统派
moderno|现代
modernos|现代
contemporaneo|当代
moderna|现代
nova|新式
nuevo|新式
nu-cumbia|新坎比亚
neo classical metal|新古典金属
neo-progressive|新前卫摇滚
neo metal|新派金属
neo-rockabilly|新乡村摇滚
neofolk|新民谣
neo-pagan|新异教主题音乐
mod revival|摩德复兴
modern mod|当代摩德音乐
deathrock|死亡摇滚
deathrash|死亡鞭击金属
death 'n' roll|死亡金属摇滚融合
black 'n' roll|黑金属摇滚融合
black death|黑金属与死亡金属融合
blackgaze|黑金属与盯鞋融合
post-black metal|后黑金属
post-doom metal|后厄运金属
doomgaze|厄运金属与盯鞋融合
depressive black metal|抑郁黑金属
dissonant death metal|不协和死亡金属
slam death metal|重击死亡金属
slamming deathcore|重击死核
brutal deathcore|残酷死核
crossover thrash|跨界鞭击金属
pagan black metal|异教黑金属
oriental metal|东方元素金属
cyber metal|赛博电子金属
sci-fi metal|科幻主题金属
nwothm|传统重金属新浪潮
nwocr|经典摇滚新浪潮
usbm|美国黑金属
kawaii metal|可爱金属
post-post-hardcore|后硬核衍生音乐
crust punk|硬壳朋克
anarcho-punk|无政府主义朋克
queercore|酷儿朋克
egg punk|古怪车库朋克
ramonescore|雷蒙斯式朋克
grebo|英国另类摇滚舞曲融合
gothabilly|哥特乡村摇滚
cowpunk|乡村朋克
dance-punk|舞曲朋克
elektropunk|电子朋克
synth punk|合成器朋克
crank wave|新一代后朋克
straight edge|直刃硬核
vegan straight edge|纯素直刃硬核
beatdown|重击硬核
powerviolence|暴力强硬核
skramz|尖叫情绪核
nyhc|纽约硬核
uk82|英国八十年代朋克
goregrind|血腥主题碾核
pornogrind|成人主题碾核
drain|网络云说唱相关分支
nerdcore|极客说唱
horrorcore|恐怖主题说唱
military rap|军事主题说唱
narco rap|毒枭叙事说唱
samurai trap|武士主题陷阱音乐
necrotrap|恐怖主题陷阱音乐
futuristic swag|未来感流行说唱
westcoast flow|西海岸说唱
frauenrap|女性说唱
josei rap|日本女性说唱
zhenskiy rep|俄语女性说唱
kadin rap|女性说唱
rap femenino|女性说唱
rap feminino|女性说唱
fem rap|女性说唱
rap feminino nacional|巴西女性说唱
rap nacional|本土说唱
rap geek|极客主题说唱
rap uliczny|波兰街头说唱
rap motywacja|波兰励志说唱
smutny rap|波兰伤感说唱
rap chretien|基督教说唱
rap francais nouvelle vague|法国新浪潮说唱
oldschool deutschrap|老派德国说唱
suomirap|芬兰说唱
nephop|尼泊尔嘻哈
chopped and screwed|降速切碎混音嘻哈
trap queen|女性陷阱说唱
aesthetic rap|美学氛围说唱
speed plug brasileiro|巴西加速柔和陷阱说唱
traphall|陷阱说唱与舞厅雷鬼融合
basshall|低音舞厅雷鬼融合
asakaa|加纳钻头说唱
hiplife|加纳嘻哈与高寿音乐融合
gengetone|肯尼亚都市舞曲
hipco|利比里亚嘻哈
turntablism|唱盘主义
scratch|唱盘搓碟
beatboxing|口技节奏
2-step|两步车库舞曲
speed garage|高速车库舞曲
speed house|高速浩室
jackin' house|切分放克浩室
soulful house|灵魂浩室
fidget house|抖动音色浩室
beach house|海滩氛围浩室
vinahouse|越南浩室
bolobedu house|南非博洛贝杜浩室
ghettotech|街区科技舞曲
footwork|芝加哥脚步舞曲
hardgroove|强律动科技舞曲
hardtekk|硬派快速电子
schranz|硬派循环科技舞曲
bleep techno|哔声科技舞曲
proto-techno|早期科技舞曲
acidcore|酸性硬核电子
raggatek|雷鬼硬派电子
freeform hardcore|自由型硬核电子
mashcore|拼接硬核电子
jumpstyle|跳步舞曲
tekno|地下锐舞电子
nu gabber|新加巴硬核电子
drill and bass|繁复碎拍电子
nu skool breaks|新派碎拍
funky breaks|放克碎拍
halftime dnb|半拍鼓打贝斯
jazzy dnb|爵士鼓打贝斯
atmospheric dnb|氛围鼓打贝斯
dnb|鼓打贝斯
darkstep|暗黑鼓打贝斯
neurostep|神经音色回响贝斯
deathstep|极重型回响贝斯
filthstep|粗粝回响贝斯
tearout|爆裂回响贝斯
riddim dubstep|重复低音回响贝斯
chillstep|舒缓回响贝斯
chill out|放松电子
chill-out|放松电子
psychill|迷幻舒缓电子
dream trance|梦幻迷幻舞曲
tech trance|科技迷幻舞曲
covertrance|翻唱迷幻舞曲
melbourne bounce|墨尔本弹跳舞曲
melbourne bounce international|国际墨尔本弹跳舞曲
future bounce|未来弹跳舞曲
future funk|未来放克
funky tech house|放克科技浩室
groove house|律动浩室
synth funk|合成器放克
synth prog|合成器前卫摇滚
synth|合成器音乐
synthesizer|合成器音乐
modular synth|模块化合成器音乐
moog|穆格合成器
minimal wave|极简新浪潮
horror synth|恐怖合成器音乐
dungeon synth|地牢合成器音乐
sovietwave|苏联复古电子
vaportrap|蒸汽陷阱电子
slushwave|朦胧蒸汽波
mallsoft|商场氛围蒸汽波
broken transmission|广播拼贴蒸汽波
utopian virtual|虚拟乌托邦电子
aggrotech|侵略性工业电子
martial industrial|军事主题工业音乐
hauntology|怀旧幽灵感音乐
plunderphonics|采样拼贴音乐
mashup|歌曲混搭
collage pop|拼贴流行
jamtronica|即兴电子
wave|波系电子音乐
fourth world|第四世界民族电子融合
exotica|异国情调沙发音乐
rare groove|稀有放克灵魂乐
balearic|巴利阿里式舞曲
nu age|新世纪音乐衍生
k-rap|韩国说唱
j-rap|日本说唱
v-pop|越南流行
p-pop|菲律宾流行
hk-pop|香港流行
scandipop|北欧流行
k-rock|韩国摇滚
k-indie|韩国独立音乐
j-indie|日本独立音乐
j-acoustic|日本原声音乐
j-ambient|日本氛围音乐
j-punk|日本朋克
j-metal|日本金属
j-reggae|日本雷鬼
j-core|日本硬核电子
j-poprock|日本流行摇滚
j-idol|日本偶像音乐
j-pixie|日本流行朋克相关分支
j-division|日本另类摇滚相关分支
chinese minyao|中国民谣
chinese manyao|华语慢摇舞曲
taiwan campus folk|台湾校园民歌
er ge|儿歌
k-pop reality show|韩国偶像真人秀音乐
48g|48系偶像团体音乐
touhou|东方Project同人音乐
bemani|Bemani音游音乐
doujin|同人音乐
twee pop|甜美纯真独立流行
dreamgaze|梦幻盯鞋
popgaze|流行盯鞋
dreamo|梦幻情绪摇滚
bubblegrunge|明快旋律垃圾摇滚
beatlesque|披头士式流行摇滚
brill building pop|布里尔大厦流行
tin pan alley|锡盘巷流行歌曲
lilith|女性唱作人相关音乐
ectofolk|女性唱作民谣相关音乐
cosmic american|美国乡村与迷幻融合
middle earth|中土奇幻主题音乐
fantasy|奇幻主题音乐
pirate|海盗主题音乐
music hall|歌舞杂耍音乐
comedie musicale|法语音乐剧
operetta|轻歌剧
comedia|喜剧音频
kabarett|德语讽刺歌舞
cabaret|歌舞表演音乐
clean comedy|无露骨内容喜剧
humour francais|法语幽默音频
chanson humoristique|法语诙谐歌曲
chanson paillarde|法语俚俗歌曲
children's story|儿童故事音频
children's choir|儿童合唱
comptine|法语童谣
bornesange|丹麦儿童歌曲
detskie pesni|俄语儿童歌曲
detske pisnicky|捷克儿童歌曲
gyerekdalok|匈牙利儿童歌曲
musik anak-anak|印尼儿童歌曲
muzika l'yeladim|希伯来语儿童音乐
paidika tragoudia|希腊儿童歌曲
kodomo no ongaku|日本儿童音乐
musiikkia lapsille|芬兰儿童音乐
musica para criancas|葡语儿童音乐
histoire pour enfants|法语儿童故事
zespol dzieciecy|波兰儿童合唱团
cancion infantil|西语儿童歌曲
chinderlieder|瑞士德语儿童歌曲
vlaamse kinderliedje|弗拉芒语儿童歌曲
marathi balgeet|马拉地语儿童歌曲
vintage radio show|老广播节目
german literature|德语文学朗读
slam poetry|诗歌竞演
poezja spiewana|波兰吟唱诗歌
sung poetry|吟唱诗歌
gaita zuliana|委内瑞拉苏利亚盖塔音乐
calypso|卡利普索音乐
chutney|加勒比印度裔舞曲
bouyon|多米尼克布永舞曲
dennery segment|圣卢西亚丹纳里舞曲
trinibad|特立尼达舞厅雷鬼
shatta|法属加勒比舞厅音乐
riddim|雷鬼节奏型音乐
cubaton|古巴雷鬼顿
rkt|阿根廷雷鬼顿与坎比亚融合
guaracha|瓜拉恰舞曲
boogaloo|拉丁布加洛
cha-cha-cha|恰恰舞曲
danzon|古巴丹松舞曲
charanga|古巴查兰加乐团
porro|哥伦比亚波罗舞曲
champeta|哥伦比亚查姆佩塔舞曲
huapango|墨西哥瓦潘戈舞曲
copla|西班牙叙事歌谣
nuevo flamenco|新弗拉门戈
sevillanas|塞维利亚舞曲
nuevo tango|新探戈
neotango|新派探戈
zamba|阿根廷桑巴民间舞曲
cueca chilena|智利奎卡舞曲
carimbo|巴西卡林博舞曲
baiao|巴西巴伊昂舞曲
coco|巴西科科民间音乐
mega funk|巴西派对电子放克
fogo pentecostal|巴西五旬节派敬拜音乐
louvores pentecostais|五旬节派赞美诗歌
adoracion pentecostal|五旬节派敬拜音乐
adoracion|敬拜音乐
adventista|基督复临派宗教音乐
apostolic worship|使徒派敬拜音乐
world devotional|世界宗教敬拜音乐
devotional|宗教颂赞
family gospel|家庭组合福音
coral gospel|福音合唱
gospel singers|福音歌手
muzica crestina|罗马尼亚基督教音乐
christelijk|荷兰基督教音乐
messianic praise|弥赛亚派赞美音乐
anglican liturgy|圣公会礼仪音乐
orthodox chant|东正教圣咏
chant religieux|宗教吟诵
jewish cantorial|犹太领唱圣歌
psalmen|诗篇颂唱
zikir|伊斯兰记主吟诵
naat|伊斯兰赞圣诗
ilahiler|土耳其伊斯兰赞歌
latmiya|什叶派悼念颂唱
rosary|玫瑰经祈祷音频
umbanda|巴西乌班达宗教音乐
candomble|巴西坎东布雷宗教音乐
chinese wind|中国民族吹管乐
oud|乌德琴
sitar|西塔琴
bouzouki|布祖基琴
charango|恰朗戈琴
cuatro venezolano|委内瑞拉四弦琴
cuatro puertorriqueno|波多黎各四弦琴
bandoneon|班多钮手风琴
accordeon|手风琴
sanfona|巴西手风琴
harpsichord|羽管键琴
hammond organ|哈蒙德电风琴
electric bass|电贝斯
double bass|低音提琴
trombone|长号
vibraphone|颤音琴
tuba|大号
horn|圆号
didgeridoo|迪吉里杜管
singing bowl|颂钵
jaw harp|口簧琴
slack-key guitar|夏威夷松弦吉他
guitarra portuguesa|葡萄牙吉他
guitarra andina|安第斯吉他
guitarra mexicana|墨西哥吉他
viola caipira|巴西乡村十弦吉他
violao classico|古典吉他
tololoche|墨西哥托洛洛切低音琴
double drumming|双鼓手演奏
string duo|弦乐二重奏
chamber orchestra|室内乐团
quatuor a cordes|弦乐四重奏
quartetto d'archi|弦乐四重奏
streichquartett|弦乐四重奏
quarteto|四重奏
polyphony|复调音乐
galante era|华丽风格时期古典音乐
21st century classical|二十一世纪古典音乐
barockinterpreten|巴洛克音乐演奏
symfonicky orchestr|交响乐团
orkiestra symfoniczna|交响乐团
guggenmusik|瑞士狂欢节管乐
blasmusik|德语地区管乐
blaskapelle|德语地区管乐团
cornetas y tambores|号角与鼓乐
banda de viento|管乐团
banda militar|军乐队
musique militaire|军乐
orquesta tipica|传统乐团
college a cappella|大学无伴奏合唱
kinderchor|儿童合唱
jugendchor|青年合唱
kerkkoor|教堂合唱
military|军事主题
early|早期
smooth|柔和流畅
international|国际
western|西部
midwest|美国中西部
east coast|东海岸
west coast|西海岸
alt|另类
new school|新派
oldschool|老派
acustico|原声
independant|独立
alternatif|另类
gotico|哥特
progressif|前卫
progresivo|前卫
virale|网络热门
indigena|原住民
indigenous|原住民
super|高能
gym|健身向
kawaii|可爱系
christian uplift|基督教励志音乐
motivational|励志
motivation|励志音乐
hard motivation|强节拍励志音乐
football|足球歌曲
fussball|足球歌曲
voetbal|足球歌曲
fotbollslatar|足球歌曲
fan chant|球迷助威歌
sound effects|音效
library music|素材库配乐
cover acustico|原声翻唱
coverchill|舒缓翻唱
covertronica|电子翻唱
speed up|加速版音乐
christmas product|圣诞主题音乐
remix product|混音版音乐
karaoke|卡拉OK伴奏
lo-fi product|低保真背景音乐
background jazz product|爵士背景音乐
guided meditation|引导冥想音频
spa|水疗背景音乐
528hz|528赫兹主题音频（非疗效承诺）
432hz|432赫兹主题音频（非疗效承诺）
tone|单音音频
manila sound|马尼拉流行之声
kundiman|菲律宾传统情歌
keroncong|印尼克隆宗民间音乐
campursari|爪哇混合民间音乐
rumba congolaise|刚果伦巴
ndombolo|刚果恩东博洛舞曲
soukous|刚果苏库斯舞曲
makossa|喀麦隆马科萨舞曲
mbalax|塞内加尔姆巴拉克斯
zouglou|科特迪瓦祖格鲁舞曲
coupe-decale|科特迪瓦库佩代卡莱舞曲
semba|安哥拉森巴舞曲
funana|佛得角富纳纳舞曲
morna|佛得角莫尔纳歌曲
sega mauricien|毛里求斯塞卡音乐
batida|葡语非洲电子舞曲
singeli|坦桑尼亚高速电子舞曲
ethio-jazz|埃塞俄比亚爵士
rebetiko|希腊雷贝蒂科
mizrahi|以色列东方犹太音乐
kabyle|卡比尔音乐
khaleeji iraqi|伊拉克海湾音乐
bozlak|土耳其博兹拉克民间歌唱
turk sanat muzigi|土耳其艺术音乐
turkce slow sarkilar|土耳其语慢歌
huzunlu sarkilar|土耳其伤感歌曲
oyun havasi|土耳其民间舞曲
karadeniz turkuleri|土耳其黑海民歌
narodna muzika|巴尔干民间音乐
narodnozabavna|斯洛文尼亚民间流行
muzica populara|罗马尼亚民间音乐
muzica usoara|罗马尼亚轻流行
muzica lautareasca|罗马尼亚乐师民间音乐
neomelodici|那不勒斯新旋律流行
puirt-a-beul|苏格兰盖尔语口传舞曲
yodeling|约德尔唱法
alpine yodeling|阿尔卑斯约德尔歌唱
ceilidh|凯利民间社交舞音乐
jig and reel|吉格与里尔民间舞曲
skansk musik|瑞典斯科讷音乐
norske viser|挪威叙事歌谣
visor|北欧叙事歌谣
papuri|菲律宾赞美音乐
waiata maori|毛利歌曲
kapa haka|毛利哈卡歌舞
rabindra sangeet|泰戈尔歌曲
khayal|印度卡亚尔古典声乐
rakugo|日本落语
canzone napoletana|那不勒斯歌曲
canzone genovese|热那亚歌曲
cancion melodica|西语抒情歌曲
novos talentos brasileiros|巴西新晋音乐人
novos|新晋
nova musica|新派音乐
musica popular|通俗音乐
musica antiga|古乐
musica antigua|古乐
musique ancienne|古乐
musica tradicional|传统音乐
musica indigena|原住民音乐
musica etnica|民族音乐
musica sinfonica|交响乐
musica llanera|南美草原民间音乐
musica andina|安第斯音乐
musica criolla|克里奥尔音乐
musica sarda|撒丁岛音乐
musica gaucha tradicionalista|巴西南部传统高乔音乐
regional mexicano femenil|女性墨西哥地方音乐
pop teen|青少年流行
vocal harmony group|人声和声组合
gospel antigas|经典福音音乐
funk das antigas|早期巴西放克
forro de favela|巴西社区弗罗舞曲
batidao romantico|巴西浪漫节拍舞曲
baile|巴西舞会音乐
lagu jawa|爪哇歌曲
lagu timur|印尼东部歌曲
lagu melayu|马来歌曲
lagu sunda|巽他歌曲
lagu bali|巴厘歌曲
lagu bugis|布吉歌曲
lagu aceh|亚齐歌曲
lagu sasak|萨萨克歌曲
lagu karo|卡罗歌曲
lagu manado|万鸦老歌曲
lagu iban|伊班歌曲
lagu maluku|马鲁古歌曲
lagu betawi|巴达维歌曲
lagu jambi|占碑歌曲
lagu lampung|楠榜歌曲
lagu madura|马都拉歌曲
lagu sabahan|沙巴歌曲
lagu tarling|印尼吉他长笛民间音乐
afrikaans|南非荷兰语音乐
hawaiian|夏威夷音乐
sami|萨米音乐
sindhi|信德语音乐
maghreb|马格里布音乐
khmer|高棉音乐
xhosa|科萨语音乐
esperanto|世界语音乐
cymraeg|威尔士语音乐
maithili|迈蒂利语音乐
gypsy|罗姆人音乐
batak|巴塔克音乐
kavkaz|高加索音乐
rif|里夫地区音乐
austropop|奥地利流行
austindie|奥斯汀独立音乐
black americana|黑人美式根源音乐
black thrash|黑金属与鞭击融合
black punk|黑金属与朋克融合
black speed metal|黑金属与速度金属融合
black sludge|黑金属与泥浆金属融合
black noise|黑金属噪音融合
black comedy|黑人喜剧表演
indie game soundtrack|独立游戏配乐
folk cantabria|坎塔布里亚民间音乐
canadian latin|加拿大拉丁音乐
viking folk|维京主题民谣
rune folk|北欧符文主题民谣
geek folk|极客主题民谣
geek rock|极客主题摇滚
freak folk|怪诞民谣
chamber folk|室内民谣
queer country|酷儿乡村
truck-driving country|卡车司机主题乡村
cowboy western|西部牛仔音乐
bush ballad|澳洲丛林叙事歌
american primitive|美国原始主义指弹
early avant garde|早期先锋音乐
avant-rock|先锋摇滚
krautrock|德国实验摇滚
canterbury scene|坎特伯雷前卫摇滚
hamburger schule|汉堡独立摇滚学派
modular techno|模块化科技舞曲
hypnotic techno|催眠感科技舞曲
goa psytrance|果阿迷幻电子
psybass|迷幻低音电子
psydub|迷幻Dub混音
spacesynth|太空合成器舞曲
psych gaze|迷幻盯鞋
new wave of thrash metal|鞭击金属新浪潮
new wave of glam metal|华丽金属新浪潮
new wave of osdm|老派死亡金属新潮
neo-crust|新硬壳朋克
crust|硬壳朋克
d-beat|D节拍硬核朋克
thrash core|极速硬核朋克
ukhc|英国硬核
japanoise|日本噪音音乐
no beat|无鼓点音乐
lo star|低保真独立音乐标签
outsider|局外人音乐
outsider house|局外人浩室
kindie rock|儿童独立摇滚
boy pop|男子组合流行
t-pop girl group|泰国女子组合流行
tropical tecladista|热带键盘音乐
israeli mediterranean|以色列地中海音乐
belly dance|肚皮舞音乐
bandinhas|巴西小型舞会乐队
glee club|合唱社团音乐
danseband|北欧舞厅乐队音乐
danspunk|北欧舞厅朋克融合
griot|西非口传艺人音乐
muzica etno|罗马尼亚民族流行
muzica copii|罗马尼亚儿童音乐
cancoes infantis|葡语儿童歌曲
cuento infantile|西语儿童故事
detske pesnicky|斯洛伐克儿童歌曲
kids dance party|儿童派对舞曲
bachchon ke geet|印地语儿童歌曲
vaikiskos dainos|立陶宛儿童歌曲
detski pesnichki|保加利亚儿童歌曲
aghani lil-atfal|阿拉伯语儿童歌曲
waiata mo tamariki|毛利儿童歌曲
musique pour enfant quebecois|魁北克儿童音乐
bornehistorier|丹麦儿童故事
barnasogur|冰岛儿童故事
barnalog|冰岛儿童歌曲
cartoni animati|意大利动画音乐
dessin anime|法语动画音乐
contrabass|低音提琴
shamisen|三味线
erhu|二胡
panpipe|排箫
bansuri|印度竹笛
ney|中东奈伊笛
mbira|姆比拉拇指琴
cimbalom|钦巴龙扬琴
cifteli|阿尔巴尼亚双弦琴
tar|塔尔长颈弹拨琴
tulum|土耳其风笛
zampogna|意大利风笛
kaba gaida|保加利亚卡巴风笛
kantele|芬兰康特勒琴
washboard|洗衣板打击乐
chapman stick|查普曼触弦琴
arpa paraguaya|巴拉圭竖琴
arpa grande|墨西哥大竖琴
schwyzerorgeli|瑞士小手风琴
heligonka|中欧按钮手风琴
trikiti|巴斯克手风琴
trekkspill|挪威手风琴
dragspel|瑞典手风琴
throat singing|喉音歌唱
traditional irish singing|爱尔兰传统歌唱
barbershop|理发店四重唱
madrigal|牧歌合唱
sacred harp|圣竖琴传统合唱
spirituals|黑人灵歌
ragtime|拉格泰姆
boogie-woogie|布吉伍吉
stride|跨步钢琴爵士
straight-ahead jazz|传统主流爵士
spiritual jazz|灵性爵士
ethereal|空灵
cosmic|宇宙感
cinematic|电影感
warm|温暖
heavy|重型
light music|轻音乐
ritual|仪式
modular|模块化
pre-war|战前
cavernous|洞穴混响感
cryptic|晦暗神秘
grim|阴森
grisly|恐怖粗粝
charred death|焦灼粗粝死亡金属标签
active rock|电台热门摇滚
sleaze rock|粗犷华丽摇滚
trop rock|热带风情摇滚
swamp pop|路易斯安那沼泽流行
hardtechno|硬派科技舞曲
trad|传统
twee|甜美纯真
neo|新式
nu|新派
classic female blues|经典女性布鲁斯
female|女性
chamber|室内乐式
spiritual|灵性主题
emotional|情绪化
viking|维京主题
indie fuzzpop|失真独立流行
bl|男同性恋题材
musicals|音乐剧
composition|作曲
singing|歌唱
salon music|沙龙音乐
salon|沙龙
chill groove|舒缓律动音乐
death industrial|死亡工业噪音
math pop|数学流行
crack rock steady|硬壳朋克与稳拍融合
latincore|拉丁重型音乐融合
electro trash|粗粝电子音乐
high-tech minimal|高技术极简科技舞曲
bubblegum bass|泡泡糖低音电子
makina|西班牙快节奏舞曲
nitzhonot|旋律迷幻舞曲分支
forest psy|森林系迷幻舞曲
new isolationism|孤寂氛围音乐
dronescape|持续音音景
somatik techno|Somatik科技舞曲分支
serialism|序列主义音乐
fictitious orchestra|虚构乐团录音标签
guitar case|吉他音乐细分标签
glass|玻璃乐器音乐
animal singing|动物叫声音乐
language|语言类音频
bible|圣经朗读
erotica|成人情欲主题音频
erotik|成人情欲主题音频
erotic product|成人情欲主题音频
comptine africaine|非洲童谣
song poem|谱曲诗歌
antiviral pop|网络趣味流行
musical advocacy|倡议主题音乐
christlicher rap|德语基督教说唱
louange|法语赞美音乐
psalms|诗篇颂唱
baptist gospel|浸信会福音音乐
musica bautista|浸信会音乐
muzica bisericeasca|罗马尼亚教会音乐
musicas espiritas|巴西灵性宗教音乐
musica crista reformada|改革宗基督教音乐
muzica moldoveneasca|摩尔多瓦民间音乐
musica de intervencao|葡语社会抗议音乐
nueva ola|拉丁新浪潮流行
nueva trova|新吟唱歌曲
nova canco|加泰罗尼亚新歌运动
canto popular|民间歌唱
feminino|女性
alternativos|另类
pesado|重型
evangelico|福音
evangelica|福音
melodico|旋律
andina|安第斯
afrocolombiano|非洲哥伦比亚
afroperuana|非洲秘鲁
portuguesa contemporanea|当代葡萄牙
noir|黑金属
clasico|经典
musique traditionnelle|传统音乐
musica prehispanica|西班牙殖民前美洲音乐
musica occitana|奥克语地区音乐
musica mapuche|马普切音乐
musica purepecha|普雷佩查音乐
musica wixarika|维克萨里卡音乐
musica mixteca|米斯特克音乐
musica rapa nui|复活节岛拉帕努伊音乐
musique touareg|图阿雷格音乐
musique mandingue|曼丁音乐
musique peule|富拉音乐
musique soninke|索宁克音乐
pygmy music|中非森林族群音乐
cerkes muzikleri|切尔克斯音乐
orquesta cubana|古巴乐团
orquesta tropical|热带拉丁乐团
musica nortena chilena|智利北部音乐
musica portuguesa contemporanea|葡萄牙当代音乐
musica hondurena|洪都拉斯音乐
musica nicaraguense|尼加拉瓜音乐
musica canaria|加那利群岛音乐
musique tahitienne|塔希提音乐
musique acadienne|阿卡迪亚音乐
jazz caraibes|加勒比爵士
canto a tenore|撒丁岛男声复调
georgian polyphony|格鲁吉亚复调
albanian iso polyphony|阿尔巴尼亚持续低音复调
polyphonies corses|科西嘉复调合唱
trallalero|热那亚多声部合唱
himene tarava|塔希提复调圣歌
bothy ballad|苏格兰农舍叙事歌
koledy|波兰圣诞颂歌
villancicos|西语圣诞颂歌
noel quebecois|魁北克圣诞音乐
japanese buddhist chant|日本佛教吟诵
korean minyo|韩国民谣
ryukyu ongaku|琉球音乐
tan co|越南新古融合歌唱
tanci|弹词
marimba de guatemala|危地马拉马林巴音乐
marimba orquesta|马林巴乐团
scenecore|网络Scene文化电子音乐
weirdcore|怪诞网络美学音乐
sigilkore|失真网络说唱分支
pixel|像素电玩音乐相关标签
shush|安静背景音标签
speedrun|游戏速通相关音乐标签
`.trim().split('\n').map(line => line.split('|')));

const prefixes = Object.fromEntries(`
american|美国
british|英国
uk|英国
english|英格兰
irish|爱尔兰
scottish|苏格兰
welsh|威尔士
french|法国
german|德国
italian|意大利
spanish|西班牙
portuguese|葡萄牙
dutch|荷兰
belgian|比利时
swiss|瑞士
austrian|奥地利
swedish|瑞典
norwegian|挪威
finnish|芬兰
danish|丹麦
icelandic|冰岛
russian|俄罗斯
ukrainian|乌克兰
belarusian|白俄罗斯
polish|波兰
czech|捷克
slovak|斯洛伐克
hungarian|匈牙利
romanian|罗马尼亚
bulgarian|保加利亚
greek|希腊
serbian|塞尔维亚
croatian|克罗地亚
slovenian|斯洛文尼亚
bosnian|波斯尼亚
albanian|阿尔巴尼亚
estonian|爱沙尼亚
latvian|拉脱维亚
lithuanian|立陶宛
turkish|土耳其
kurdish|库尔德
arab|阿拉伯
arabic|阿拉伯语
persian|波斯
iranian|伊朗
israeli|以色列
hebrew|希伯来语
lebanese|黎巴嫩
syrian|叙利亚
egyptian|埃及
moroccan|摩洛哥
algerian|阿尔及利亚
tunisian|突尼斯
african|非洲
south african|南非
nigerian|尼日利亚
ghanaian|加纳
kenyan|肯尼亚
ethiopian|埃塞俄比亚
senegalese|塞内加尔
congolese|刚果
angolan|安哥拉
canadian|加拿大
mexican|墨西哥
brazilian|巴西
argentine|阿根廷
argentinian|阿根廷
chilean|智利
colombian|哥伦比亚
peruvian|秘鲁
venezuelan|委内瑞拉
uruguayan|乌拉圭
bolivian|玻利维亚
ecuadorian|厄瓜多尔
cuban|古巴
puerto rican|波多黎各
dominican|多米尼加
jamaican|牙买加
haitian|海地
latin|拉丁
latin american|拉丁美洲
australian|澳大利亚
new zealand|新西兰
indian|印度
pakistani|巴基斯坦
bangladeshi|孟加拉国
bengali|孟加拉语
hindi|印地语
tamil|泰米尔语
telugu|泰卢固语
punjabi|旁遮普语
nepali|尼泊尔
sri lankan|斯里兰卡
chinese|中国
mandarin|国语
cantonese|粤语
taiwanese|台湾
hong kong|香港
japanese|日本
korean|韩国
vietnamese|越南
thai|泰国
indonesian|印度尼西亚
malaysian|马来西亚
singaporean|新加坡
filipino|菲律宾
pinoy|菲律宾
cambodian|柬埔寨
mongolian|蒙古
tibetan|藏族
uyghur|维吾尔族
kazakh|哈萨克
uzbek|乌兹别克
georgian|格鲁吉亚
armenian|亚美尼亚
azerbaijani|阿塞拜疆
argentina|阿根廷
argentino|阿根廷
brasileiro|巴西
brasileira|巴西
brasilero|巴西
brasil|巴西
francais|法语
francaise|法语
francophone|法语
italiano|意大利
italiana|意大利
siciliano|西西里
siciliana|西西里
napoletano|那不勒斯
napoletana|那不勒斯
genovese|热那亚
sardegna|撒丁岛
sardinia|撒丁岛
toscana|托斯卡纳
espanol|西班牙语
en espanol|西班牙语
colombiano|哥伦比亚
colombiana|哥伦比亚
chileno|智利
chilena|智利
mexicano|墨西哥
mexicana|墨西哥
peruano|秘鲁
peruana|秘鲁
ecuatoriano|厄瓜多尔
ecuatoriana|厄瓜多尔
venezolano|委内瑞拉
venezolana|委内瑞拉
venezuela|委内瑞拉
uruguayo|乌拉圭
uruguaya|乌拉圭
paraguayo|巴拉圭
paraguaya|巴拉圭
boliviano|玻利维亚
boliviana|玻利维亚
dominicano|多米尼加
dominicana|多米尼加
puertorriquena|波多黎各
puertorriqueno|波多黎各
boricua|波多黎各
cubano|古巴
cubana|古巴
panameno|巴拿马
panamanian|巴拿马
tico|哥斯达黎加
tica|哥斯达黎加
nica|尼加拉瓜
nicaraguan|尼加拉瓜
catracho|洪都拉斯
guatemalteca|危地马拉
guatemalan|危地马拉
salvadoreno|萨尔瓦多
salvadoran|萨尔瓦多
latinoamericano|拉丁美洲
latinoamericana|拉丁美洲
central american|中美洲
portugues|葡萄牙
tuga|葡萄牙
catala|加泰罗尼亚
catalana|加泰罗尼亚
catalan|加泰罗尼亚
canario|加那利群岛
euskera|巴斯克语
euskal|巴斯克
basque|巴斯克
galician|加利西亚
galego|加利西亚
andaluz|安达卢西亚
andalusian|安达卢西亚
asturiana|阿斯图里亚斯
cantabria|坎塔布里亚
extremeno|埃斯特雷马杜拉
extremena|埃斯特雷马杜拉
magyar|匈牙利
czsk|捷克与斯洛伐克
belge|比利时
quebecois|魁北克
quebec|魁北克
montrealais|蒙特利尔
montreal|蒙特利尔
nz|新西兰
kiwi|新西兰
aussie|澳大利亚
taiwan|台湾
hk|香港
mainland chinese|中国大陆
viet|越南
turkce|土耳其语
azeri|阿塞拜疆
suomi|芬兰
svensk|瑞典
dansk|丹麦
nordic|北欧
scandinavian|斯堪的纳维亚
baltic|波罗的海地区
balkan|巴尔干
kosovan|科索沃
macedonian|北马其顿
faroese|法罗群岛
maltese|马耳他
luxembourgian|卢森堡
moldovan|摩尔多瓦
cypriot|塞浦路斯
ua|乌克兰
chechen|车臣
tatar|鞑靼
yakut|雅库特
tuvan|图瓦
caucasian|高加索
circassian|切尔克斯
central asian|中亚
tajik|塔吉克
turkmen|土库曼
kyrgyz|吉尔吉斯
afghan|阿富汗
iraqi|伊拉克
yemeni|也门
libyan|利比亚
algerien|阿尔及利亚
tunisien|突尼斯
maroc|摩洛哥
palestinian|巴勒斯坦
maghreb|马格里布
hawaiian|夏威夷
okinawan|冲绳
native american|美洲原住民
asian american|亚裔美国
african american|非裔美国
jewish|犹太
afrikaner|阿非利卡
afrikaans|南非荷兰语
urdu|乌尔都语
bhojpuri|博杰普尔语
gujarati|古吉拉特语
haryanvi|哈里亚纳语
odia|奥里亚语
marathi|马拉地语
assamese|阿萨姆语
malayalam|马拉雅拉姆语
kannada|卡纳达语
bangla|孟加拉语
bangali|孟加拉语
west bengali|西孟加拉
himachali|喜马偕尔
garhwali|加瓦利语
rajasthani|拉贾斯坦
kashmiri|克什米尔
konkani|孔卡尼语
saraiki|萨莱基语
sindhi|信德语
dogri|多格拉语
ladakhi|拉达克
bhutanese|不丹
sinhala|僧伽罗语
hausa|豪萨语
igbo|伊博语
yoruba|约鲁巴语
kikuyu|基库尤语
sesotho|塞索托语
xhosa|科萨语
oromo|奥罗莫语
malagasy|马达加斯加
sundanese|巽他
javanese|爪哇
balinese|巴厘岛
bisaya|米沙鄢语
ilocano|伊洛卡诺语
tagalog|他加禄语
khmer|高棉
lao|老挝
myanmar|缅甸
burmese|缅甸
bruneian|文莱
chamorro|查莫罗
inuit|因纽特
polynesian|波利尼西亚
tahitian|塔希提
tongan|汤加
papuan|巴布亚
samoan|萨摩亚
maldivian|马尔代夫
beninese|贝宁
togolese|多哥
burkinabe|布基纳法索
gabonese|加蓬
liberian|利比里亚
namibian|纳米比亚
botswana|博茨瓦纳
swazi|斯威士
ugandan|乌干达
rwandan|卢旺达
burundian|布隆迪
tanzanian|坦桑尼亚
zambian|赞比亚
zim|津巴布韦
malawian|马拉维
malian|马里
cameroonian|喀麦隆
surinamese|苏里南
seychelles|塞舌尔
barbadian|巴巴多斯
bajan|巴巴多斯
grenada|格林纳达
south sudanese|南苏丹
sudanese|苏丹
baiano|巴伊亚
baiana|巴伊亚
carioca|里约热内卢
rj|里约热内卢
paulista|圣保罗
abc paulista|圣保罗ABC地区
gaucho|南里奥格兰德
gaucha|南里奥格兰德
mineiro|米纳斯吉拉斯
bh|贝洛奥里藏特
cearense|塞阿拉
pernambucano|伯南布哥
pernambucana|伯南布哥
paraense|帕拉
paraibano|帕拉伊巴
catarinense|圣卡塔琳娜
potiguar|北里奥格兰德
sergipano|塞尔希培
sergipana|塞尔希培
alagoano|阿拉戈斯
alagoana|阿拉戈斯
goiano|戈亚斯
goiana|戈亚斯
paranaense|巴拉那
fluminense|里约州
brasiliense|巴西利亚
amazonense|亚马孙
maranhense|马拉尼昂
piauiense|皮奥伊
amapaense|阿马帕
rondoniense|朗多尼亚
roraimense|罗赖马
mato-grossense|马托格罗索
sul-mato-grossense|南马托格罗索
sinaloense|锡那罗亚
sonorense|索诺拉
chihuahuense|奇瓦瓦
tamaulipeca|塔毛利帕斯
neoleonesa|新莱昂
coahuilense|科阿韦拉
poblano|普埃布拉
poblana|普埃布拉
jalisciense|哈利斯科
chiapaneca|恰帕斯
yucateca|尤卡坦
queretano|克雷塔罗
queretana|克雷塔罗
atl|亚特兰大
atlanta|亚特兰大
nyc|纽约
new york|纽约
la|洛杉矶
los angeles|洛杉矶
philly|费城
philadelphia|费城
dfw|达拉斯沃思堡
cali|加利福尼亚
california|加利福尼亚
socal|南加州
oc|奥兰治县
chicago|芝加哥
detroit|底特律
miami|迈阿密
memphis|孟菲斯
brooklyn|布鲁克林
bronx|布朗克斯
queens|皇后区
harlem|哈莱姆
new orleans|新奥尔良
baton rouge|巴吞鲁日
boston|波士顿
seattle|西雅图
portland|波特兰
houston|休斯敦
austin|奥斯汀
san antonio|圣安东尼奥
san diego|圣迭戈
sacramento|萨克拉门托
oakland|奥克兰（美国）
bay area|旧金山湾区
pittsburgh|匹兹堡
baltimore|巴尔的摩
nashville|纳什维尔
denver|丹佛
vegas|拉斯维加斯
slc|盐湖城
st louis|圣路易斯
minneapolis|明尼阿波利斯
twin cities|明尼阿波利斯与圣保罗
cleveland|克利夫兰
buffalo|布法罗
milwaukee|密尔沃基
albuquerque|阿尔伯克基
flint|弗林特
florida|佛罗里达
texas|得克萨斯
oklahoma|俄克拉何马
kentucky|肯塔基
tennessee|田纳西
ohio|俄亥俄
virginia|弗吉尼亚
west virginia|西弗吉尼亚
minnesota|明尼苏达
arkansas|阿肯色
alabama|阿拉巴马
mississippi|密西西比
louisiana|路易斯安那
north carolina|北卡罗来纳
south carolina|南卡罗来纳
new jersey|新泽西
michigan|密歇根
wisconsin|威斯康星
indiana|印第安纳
iowa|艾奥瓦
maine|缅因
montana|蒙大拿
arizona|亚利桑那
utah|犹他
colorado|科罗拉多
idaho|爱达荷
alaska|阿拉斯加
missouri|密苏里
kansas|堪萨斯
new hampshire|新罕布什尔
south dakota|南达科他
delaware|特拉华
rhode island|罗得岛
new england|新英格兰
western ny|纽约州西部
upstate ny|纽约州北部
toronto|多伦多
vancouver|温哥华
ottawa|渥太华
calgary|卡尔加里
edmonton|埃德蒙顿
winnipeg|温尼伯
manitoba|马尼托巴
saskatchewan|萨斯喀彻温
bc|不列颠哥伦比亚
new brunswick|新不伦瑞克
atlantic canada|加拿大大西洋沿岸
cape breton|布雷顿角
london|伦敦
manchester|曼彻斯特
liverpool|利物浦
sheffield|谢菲尔德
birmingham|伯明翰
oxford|牛津
brighton|布赖顿
nottingham|诺丁汉
leicester|莱斯特
coventry|考文垂
portsmouth|朴次茅斯
swansea|斯旺西
cardiff|加的夫
belfast|贝尔法斯特
derry|德里
edinburgh|爱丁堡
dundee|邓迪
aberdeen|阿伯丁
cornwall|康沃尔
cornish|康沃尔
yorkshire|约克郡
west yorkshire|西约克郡
essex|埃塞克斯
hull|赫尔
reading|雷丁
isle of wight|怀特岛
isle of man|马恩岛
northern irish|北爱尔兰
scottish gaelic|苏格兰盖尔语
irish gaelic|爱尔兰盖尔语
cork|科克
galway|戈尔韦
melbourne|墨尔本
brisbane|布里斯班
perth|珀斯
adelaide|阿德莱德
canberra|堪培拉
auckland|奥克兰（新西兰）
wellington|惠灵顿
hamburg|汉堡
cologne|科隆
frankfurt|法兰克福
dusseldorf|杜塞尔多夫
dortmund|多特蒙德
dresden|德累斯顿
stuttgart|斯图加特
berlin|柏林
rome|罗马
milan|米兰
firenze|佛罗伦萨
bergamo|贝加莫
liguria|利古里亚
oslo|奥斯陆
bergen|卑尔根
trondheim|特隆赫姆
gothenburg|哥德堡
umea|于默奥
malmo|马尔默
kalmar|卡尔马
oulu|奥卢
prague|布拉格
brno|布尔诺
poznan|波兹南
rotterdam|鹿特丹
basel|巴塞尔
bern|伯尔尼
salzburg|萨尔茨堡
marseille|马赛
lyonnais|里昂
sevilla|塞维利亚
murcia|穆尔西亚
monterrey|蒙特雷
tijuana|蒂华纳
guadalajara|瓜达拉哈拉
chihuahua|奇瓦瓦
veracruz|韦拉克鲁斯
morelos|莫雷洛斯
merida|梅里达
concepcion|康塞普西翁
caracas|加拉加斯
brasilia|巴西利亚
belo horizonte|贝洛奥里藏特
rio grande do sul|南里奥格兰德
bangalore|班加罗尔
chennai|钦奈
pune|浦那
shanghai|上海
wuhan|武汉
northwest china|中国西北
yunnan|云南
siberian|西伯利亚
bandung|万隆
malang|玛琅
surabaya|泗水
yogyakarta|日惹
sulawesi|苏拉威西
borneo|婆罗洲
south borneo|南婆罗洲
lombok|龙目岛
pontianak|坤甸
balikpapan|巴厘巴板
bohol|保和岛
guam|关岛
us|美国
afro-cuban|非洲古巴
african-american|非裔美国
south asian|南亚
middle east|中东
middle eastern|中东
south east asian|东南亚
caribbean|加勒比
pacific islands|太平洋岛国
oceania|大洋洲
yugoslav|前南斯拉夫
slavic|斯拉夫
latinx|拉丁裔
indo|印尼
malay|马来语
minang|米南加保
mande|曼德
naija|尼日利亚
galsen|塞内加尔
angolano|安哥拉
angolana|安哥拉
congolais|刚果
guineen|几内亚
guineense|几内亚
guinean|几内亚
malien|马里
gabonais|加蓬
ivoire|科特迪瓦
mocambicana|莫桑比克
gasy|马达加斯加
mauritanien|毛里塔尼亚
mauritanienne|毛里塔尼亚
mahoraise|马约特
comorienne|科摩罗
tchadienne|乍得
centrafricaine|中非
nigerienne|尼日尔
timor-leste|东帝汶
costarricense|哥斯达黎加
salvadorena|萨尔瓦多
antillais|安的列斯
antilliaanse|安的列斯
cabo-verdiana|佛得角
cape verdean|佛得角
ecuatoguineano|赤道几内亚
ecuatoguineana|赤道几内亚
capixaba|圣埃斯皮里图
paraibana|帕拉伊巴
mineira|米纳斯吉拉斯
hokkien|闽南语
sichuanese|四川
amharic|阿姆哈拉语
swahili|斯瓦希里语
sepedi|北索托语
venda|文达语
xitsonga|聪加语
bahamian|巴哈马
fijian|斐济
gambian|冈比亚
trinidadian|特立尼达
montenegrin|黑山
jordanian|约旦
eritrean|厄立特里亚
breton|布列塔尼
sami|萨米
balochi|俾路支
maluku|马鲁古
tlaxcalteca|特拉斯卡拉
bajacaliforniana|下加利福尼亚
sudcaliforniana|南下加利福尼亚
sudcaliforniano|南下加利福尼亚
costena|沿海地区
nayarita|纳亚里特
campechana|坎佩切
campechano|坎佩切
oaxaquena|瓦哈卡
oaxaca|瓦哈卡
tabasquena|塔巴斯科
tabasqueno|塔巴斯科
guerrerense|格雷罗
michoacana|米却肯
michoacano|米却肯
quintanarroense|金塔纳罗奥
hidalguense|伊达尔戈
potosina|圣路易斯波托西
colimense|科利马
valenciana|瓦伦西亚
mallorquina|马略卡
menorquina|梅诺卡
aragonesa|阿拉贡
santomense|圣多美
madeirense|马德拉
acoriana|亚速尔
curitibano|库里蒂巴
campineiro|坎皮纳斯
campineira|坎皮纳斯
londrinense|隆德里纳
blumenauense|布卢梅瑙
marianhense|马拉尼昂
porto-alegrense|阿雷格里港
juiz-forana|茹伊斯迪福拉
feirense|费拉迪桑塔纳
pontagrossense|蓬塔格罗萨
ponta-grossense|蓬塔格罗萨
mogiana|莫吉地区
maringaense|马林加
salteno|萨尔塔
santiagueno|圣地亚哥德尔埃斯特罗
surero|阿根廷南部
tucumano|图库曼
jujeno|胡胡伊
cuyano|库约
platense|拉普拉塔
reunionnais|留尼汪
reunion|留尼汪
vincy|圣文森特
el paso|埃尔帕索
athens|雅典
tamaulipas|塔毛利帕斯
newcastle nsw|新南威尔士纽卡斯尔
ann arbor|安娜堡
eau claire|欧克莱尔
san marcos tx|得州圣马科斯
rochester mn|明州罗切斯特
rochester ny|纽约州罗切斯特
victoria bc|加拿大维多利亚
north east england|英格兰东北
asbury park|阿斯伯里帕克
jacksonville|杰克逊维尔
grand rapids|大急流城
wyoming|怀俄明
tempe|坦佩
springfield mo|密苏里斯普林菲尔德
kingston on|安大略金斯顿
ontario|安大略
alberta|艾伯塔
olympia wa|华盛顿州奥林匹亚
washington|华盛顿地区
dc|华盛顿特区
dmv|华盛顿特区及周边
rva|里士满
cdmx|墨西哥城
df|联邦区
cdo|卡加延德奥罗
kansas city|堪萨斯城
kc|堪萨斯城
okc|俄克拉何马城
ok|俄克拉何马
louisville|路易斯维尔
orlando|奥兰多
asheville|阿什维尔
gainesville|盖恩斯维尔
dayton|代顿
cincinnati|辛辛那提
omaha|奥马哈
tulsa|塔尔萨
connecticut|康涅狄格
buffalo ny|纽约州布法罗
duluth|德卢斯
eugene|尤金
long island|长岛
denton tx|得州登顿
indy|印第安纳波利斯
phoenix|菲尼克斯
charlotte nc|北卡夏洛特
tampa|坦帕
vermont|佛蒙特
new mexico|新墨西哥
fort worth|沃思堡
pennsylvania|宾夕法尼亚
charlottesville|夏洛茨维尔
western mass|马萨诸塞西部
lexington ky|肯塔基列克星敦
hamilton on|安大略汉密尔顿
windsor on|安大略温莎
dallas|达拉斯
newfoundland|纽芬兰
lafayette|拉法叶
bristol|布里斯托尔
leipzig|莱比锡
nantes|南特
glasgow|格拉斯哥
cambridgeshire|剑桥郡
cambridge|剑桥
dublin|都柏林
turin|都灵
munich|慕尼黑
granada|格拉纳达
bath|巴斯
rennes|雷恩
leeds|利兹
kent|肯特
nice|尼斯
vienna|维也纳
stockholm|斯德哥尔摩
ghent|根特
york|约克
southampton|南安普敦
devon|德文
newcastle|纽卡斯尔
graz|格拉茨
warrington|沃灵顿
uppsala|乌普萨拉
orebro|厄勒布鲁
cape town|开普敦
hokkaido|北海道
fremantle|弗里曼特尔
semarang|三宝垄
bogor|茂物
new delhi|新德里
christchurch|基督城
sydney|悉尼
dunedin|但尼丁
west australian|西澳大利亚
kolkata|加尔各答
mumbai|孟买
rosario|罗萨里奥
cordoba|科尔多瓦
sinaloa|锡那罗亚
lapland|拉普兰
lampung|楠榜
arunachal|阿鲁纳恰尔
northeast indian|印度东北
kyushu|九州
`.trim().split('\n').map(line => line.split('|')));

const tokens = Object.keys(terms).sort((a, b) => b.length - a.length);
const regions = Object.keys(prefixes).sort((a, b) => b.length - a.length);
const translations = new Map();

export function chineseGenre(name) {
  const source = String(name).trim().toLowerCase();
  if (!translations.has(source)) translations.set(source, translateGenre(source));
  return translations.get(source);
}

function translateGenre(source) {
  if (Object.hasOwn(terms, source)) return terms[source];
  // Translate only a fully recognized phrase. Never turn an unknown suffix
  // into a plausible-sounding but invented Chinese genre.
  for (const region of regions) {
    if (source.startsWith(region + ' ')) {
      const rest = chineseGenre(source.slice(region.length + 1));
      if (rest) return prefixes[region] + rest;
    }
    if (source.endsWith(' ' + region)) {
      const rest = chineseGenre(source.slice(0, -region.length - 1));
      if (rest) return prefixes[region] + rest;
    }
  }
  for (const token of tokens) {
    if (source.startsWith(token + ' ')) {
      const rest = chineseGenre(source.slice(token.length + 1));
      if (rest) return terms[token] + rest;
    }
  }
  return null;
}

// Only recognizable musical families or explicit regions may supply a partial
// hint. Never assign a sound to an opaque label from its spelling alone.
const families = `black metal|death metal|heavy metal|folk metal|metalcore|deathcore|metal|hip hop|rap|trap|drill|indie|pop|rock|punk|folk|jazz|blues|country|classical|electronic|electronica|ambient|house|techno|trance|dubstep|dnb|hardcore|reggae|reggaeton|dancehall|soul|r&b|funk|gospel|worship|choir|samba|cumbia|bachata|salsa|banda|corridos|forro|bolero|noise|soundtrack|orchestra|traditional|shoegaze|emo|bluegrass|lounge|synthpop|disco|ska`.split('|').sort((a, b) => b.length - a.length);
const readings = new Map();

export function genreReading(name) {
  const source = String(name).trim().toLowerCase();
  if (readings.has(source)) return readings.get(source);
  const translated = chineseGenre(source);
  let reading = { kind: 'untranslated', label: name };
  if (translated) {
    reading = { kind: 'translated', label: translated };
  } else {
    for (const family of families) {
      if (source.startsWith(family + ' ') || source.endsWith(' ' + family)) {
        const qualifier = source.startsWith(family + ' ') ? source.slice(family.length + 1) : source.slice(0, -family.length - 1);
        reading = { kind: 'partial', label: `${qualifier}（${terms[family]}相关）` };
        break;
      }
    }
    if (reading.kind === 'untranslated') {
      for (const region of regions) {
        if (source.startsWith(region + ' ') || source.endsWith(' ' + region)) {
          const qualifier = source.startsWith(region + ' ') ? source.slice(region.length + 1) : source.slice(0, -region.length - 1);
          reading = { kind: 'partial', label: `${prefixes[region]}音乐 · ${qualifier}` };
          break;
        }
      }
    }
  }
  reading = Object.freeze(reading);
  readings.set(source, reading);
  return reading;
}

export function genreLabel(name, language = 'zh-CN') {
  if (language === 'en') return name;
  const reading = genreReading(name);
  return reading.kind !== 'untranslated' ? `${reading.label} · ${name}` : name;
}

export function findGenre(genres, input) {
  const query = input.trim().toLowerCase();
  if (genres.has(query)) return genres.get(query);
  const matches = [...genres.values()].filter(genre =>
    genreLabel(genre.name).toLowerCase() === query || genreReading(genre.name).label.toLowerCase() === query);
  // A translated alias is not necessarily unique. Require the bilingual label
  // when two original genres share an alias instead of choosing arbitrarily.
  return matches.length === 1 ? matches[0] : undefined;
}

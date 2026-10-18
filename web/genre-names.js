// Display aliases, never identifiers. These are reading aids, not a claim that
// every Every Noise microgenre has an established Chinese name.
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
funk carioca|里约放克
baile funk|巴西放克舞曲
pagode|帕戈德桑巴
forro|福罗
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
banda|墨西哥管乐队音乐
grupera|墨西哥乐队流行
filmi|印度电影音乐
bollywood|宝莱坞电影音乐
desi|南亚
bhangra|邦格拉舞曲
qawwali|卡瓦利宗教音乐
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
chanson|法国香颂
schlager|施拉格流行
hoerspiel|广播剧
polka|波尔卡
waltz|华尔兹
marching band|行进乐队
brass band|铜管乐队
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
electronica|电子乐
metal|金属
punk|朋克
soul|灵魂乐
funk|放克
disco|迪斯科
reggae|雷鬼
ska|斯卡
gospel|福音
ambient|氛围
new age|新世纪
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
traditional|传统
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
soundtrack|原声配乐
score|影视配乐
video game music|电子游戏音乐
anime|动画
comedy|喜剧
children's music|儿童音乐
children|儿童
kids|儿童
lullaby|摇篮曲
sleep|助眠
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
bachata|巴恰塔
merengue|梅伦格
cumbia|昆比亚
bolero|波莱罗
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
phonk|Phonk 音乐
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
`.trim().split('\n').map(line => line.split('|')));

const tokens = Object.keys(terms).sort((a, b) => b.length - a.length);
const regions = Object.keys(prefixes).sort((a, b) => b.length - a.length);

export function chineseGenre(name) {
  const source = String(name).toLowerCase();
  if (terms[source]) return terms[source];
  // Translate only a fully recognized phrase. Never turn an unknown suffix
  // into a plausible-sounding but invented Chinese genre.
  for (const region of regions) {
    if (source.startsWith(region + ' ')) {
      const rest = chineseGenre(source.slice(region.length + 1));
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

export function genreLabel(name, language = 'zh-CN') {
  if (language === 'en') return name;
  const chinese = chineseGenre(name);
  return chinese ? `${chinese} · ${name}` : name;
}

export function findGenre(genres, input) {
  const query = input.trim().toLowerCase();
  if (genres.has(query)) return genres.get(query);
  const matches = [...genres.values()].filter(genre =>
    genreLabel(genre.name).toLowerCase() === query || chineseGenre(genre.name)?.toLowerCase() === query);
  // A translated alias is not necessarily unique. Require the bilingual label
  // when two original genres share an alias instead of choosing arbitrarily.
  return matches.length === 1 ? matches[0] : undefined;
}

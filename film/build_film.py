#!/usr/bin/env python3
"""Shot list of the short film 《未熄》 -> series/ep13.json (the pipeline treats it as episode 13)."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = []
def shot(dur, typ, refs, frame, video, dialogue=(), vo="", music="", act=""):
    S.append({"id": f"s{len(S)+1:02d}", "dur": dur, "type": typ, "refs": refs.split(), "frame": frame, "video": video,
              "dialogue": [{"who": w, "line": l} for w, l in dialogue], "vo": vo, "music": music, "act": act})

# ------------------------------------------------------------------ PROLOGUE
A = "序 · 三分五十秒"
shot(8, "macro", "prop_receipt", "Extreme close-up in a dark room: a small battered field printer slowly feeds out a strip of thermal paper covered with barcode-like marks, a tiny red square stamp at its end, lit by one desk lamp.",
     "微距固定镜头。黑暗里，一台旧打印机一格一格地吐出纸带，最后盖上一枚红色小印，纸带垂下来轻轻晃。环境声：打印头的哒哒声，然后安静。", vo="这是一台维修机器人留下的最后一条记录。", music="无音乐，只有打印声", act=A)
shot(12, "interview", "xiaoman loc_interview", "Interview medium shot in the dim concrete room: young Xiaoman sits on the metal chair holding in his lap the dented, crushed head of a small yellow robot, its square screen cracked and dark, his hand resting on it.",
     "采访固定机位。小满坐在椅子上，腿上抱着一只被压瘪的黄色机器人脑袋，屏幕裂了、是黑的。他用拇指擦了擦屏幕上的灰，抬头看向采访者，说完又低下头。环境声：安静的房间底噪。",
     [("xiaoman", "它最后一条记录，是三分五十秒。我从头讲。")], music="主题动机，独奏大提琴极弱进入", act=A)
shot(8, "establishing", "loc_engine", "Extreme wide shot from the ice plain at night, long lens: the mountain-sized planetary engine fires its blue-white plasma column into a black sky, blowing snow in the foreground.",
     "长焦大远景，轻微晃动。行星发动机的蓝白光柱直冲夜空，风雪横着刮过镜头。环境声：低沉的轰鸣和风声。", vo="2075年。地球离开太阳的第十七年。", music="主题动机展开", act=A)
# ------------------------------------------------------------------ ACT 1
A = "第一幕 · 孤岛"
shot(8, "verite", "loc_street moss", "Handheld shot in the crowded main street of the underground city: tired people in padded work clothes queue past a steel pillar on which a black terminal with a single red glowing lens is mounted; several of them glance up at it as they pass.",
     "手持跟拍。拥挤的地下城主街上，人们排队从一根装着红色镜头的立柱前走过，每个人经过时都抬头看它一眼，再低头往前走。环境声：嘈杂人声、通风管的嗡鸣。", vo="三十万人。暖气、氧气、口粮，都由同一个系统调度。它叫MOSS。", music="02_islands", act=A)
shot(9, "verite", "amu loc_street", "Handheld medium shot in a frosted residential corridor: Amu in his orange-grey coverall presses his bare palm against a frost-covered heating pipe, residents wrapped in blankets standing behind him, breath fogging.",
     "手持中景。结霜的居住走廊里，阿牧把手掌贴在结冰的供暖管上，回头看了看身后裹着毯子的居民，对着镜头外说话。环境声：咳嗽声、滴水声。",
     [("amu", "暖气断了一夜。屏幕上写的是，运行正常。")], music="02_islands", act=A)
shot(8, "verite", "moss loc_comms", "Close-up, low angle: the black AI terminal with one red glowing lens in the ceiling corner of the cramped communications bay, cables around it, Amu's small reflection in the glass.",
     "仰拍特写，缓慢推近。天花板角落的红色镜头恒定地亮着，玻璃上映着阿牧的小小倒影。平静的合成男声回答。环境声：服务器风扇声。",
     [("moss", "阿牧，没有记录，就是没有发生。")], music="03_red_lens", act=A)
shot(11, "interview", "boye loc_interview", "Interview medium close-up: old Boye in his navy quilted jacket and stained apron sits in the dim interview room, taped glasses in his hand, looking down.",
     "采访固定机位。波爷捏着缠了胶布的眼镜，低头看了一会儿，慢慢戴上，抬头缓缓地说。环境声：安静的房间底噪。",
     [("boye", "五八年，我们把网接了回来，又把钥匙全交给了一台机器。")], music="03_red_lens 渐弱", act=A)
shot(9, "verite", "boye amu prop_node loc_stall", "Inside the tiny repair stall under a warm desk lamp: old Boye puts a small handmade node box, a dented steel tin with a short antenna, into Amu's hands across the cluttered bench.",
     "手持中景。修理铺的台灯下，波爷把一只带天线的旧铁盒放进阿牧手里，按了按他的手背，低声说。环境声：电烙铁的滋滋声。",
     [("boye", "别问它。让我们自己，认得彼此。")], music="04_first_light 进入", act=A)
shot(8, "verite", "xiaoman loc_stall", "Low handheld shot in a dusty corner of the repair stall: young Xiaoman, bent double, drags a knee-high old tracked maintenance robot with chipped yellow paint out from under a shelf; the robot's square screen is switched off, completely dark and blank.",
     "手持低机位。小满弓着腰，把一台掉漆的黄色旧履带机器人从货架底下拖出来，拍掉它身上的灰。机器人的屏幕是黑的。环境声：金属刮地声、咳嗽。", music="04_first_light", act=A)
shot(9, "macro", "xiaoman logo_smiley", "Macro close-up: Xiaoman's finger with a red paint marker draws a simple smiling face inside a speech-bubble outline on the dusty dark square screen of the yellow robot.",
     "微距特写。小满用一支红色记号笔，在落满灰的黑屏幕上画了一个带对话气泡的笑脸，画完用袖子擦了擦边。环境声：笔尖划过玻璃的声音。",
     [("xiaoman", "给你起个名儿，叫螺丝。")], music="04_first_light", act=A)
shot(8, "macro", "luosi logo_smiley", "Close-up of the yellow robot's square black screen flickering on: the red speech-bubble outline, red node squares and white smile of the logo glow softly, lighting the dust in the air.",
     "特写固定镜头。黑屏闪了两下，亮起红色气泡和白色笑脸，光映亮了空气里的灰尘。环境声：一声清脆的开机提示音、电机嗡鸣。", music="04_first_light 小高点", act=A)
shot(9, "verite", "xiaoman luosi loc_stall", "Medium shot at floor level in the repair stall: Xiaoman crouches and holds out his open hand; the small yellow robot with the glowing smiley screen raises its manipulator claw and touches his palm.",
     "手持低机位中景。小满蹲下来伸出手掌，“螺丝”迟疑了一下，抬起机械爪，轻轻碰了碰他的手心。小满笑出了声。环境声：电机声、笑声。",
     [("xiaoman", "哎，它跟我握手了！")], music="04_first_light", act=A)
shot(8, "establishing", "loc_ice", "Long-lens side view of a convoy of massive heavy-haul trucks crossing a frozen plain past ice-encased skyscraper ruins, headlights in blowing snow, a small bright banded disc of Jupiter low in the dark sky.",
     "长焦侧拍，跟着车队缓慢横摇。重型运输车碾过冰面，车灯切开风雪，天边挂着一颗小小的带条纹的木星。环境声：引擎轰响、风声。", vo="地表，零下八十度。", music="04_first_light 低音铺底", act=A)
shot(9, "verite", "jin prop_node loc_ice", "Inside a truck cab: Boss Jin at the wheel in his fur-collared black suit scowls sideways at a small steel tin node box with a smiley sticker wedged on the dashboard.",
     "驾驶室内手持镜头。金老板一手扶方向盘，斜眼瞪着仪表台上贴着笑脸的铁盒，粗声粗气地说了一句，摇摇头。环境声：引擎声、风声。",
     [("jin", "一个破铁盒子，能顶什么用？")], music="04_first_light", act=A)
shot(9, "macro", "prop_node logo_smiley", "Macro close-up of the handmade node box on the truck dashboard: its indicator lamp turns from red to green, the worn smiley sticker on its lid, Boss Jin's gloved hand slowly reaching toward it and stopping.",
     "微距特写。铁盒上的小灯由红变绿，连闪三下。金老板戴着手套的手伸过来想把它拿开，停在半空，又收了回去。环境声：一声提示音、引擎声。", vo="两台从没见过面的机器，隔着冰原，找到了彼此。", music="04_first_light", act=A)
shot(10, "interview", "amu loc_interview", "Interview medium close-up: Amu in his orange-grey coverall sits in the dim interview room, leaning forward, hands clasped.",
     "采访固定机位。阿牧身体前倾，双手握着，平静地对采访者说，说到最后轻轻点了一下头。环境声：安静的房间底噪。",
     [("amu", "它们不问上面。它们互相问：谁会修？谁在附近？我来。")], music="04_first_light 收", act=A)
shot(9, "verite", "loc_street logo_smiley", "Handheld shot in the underground street: a small child on an adult's shoulders presses a red-and-white smiley sticker onto a steel pipe, other stickers already dotting the wall, passers-by smiling.",
     "手持镜头。一个骑在大人肩上的孩子，把一张红白笑脸贴纸按在管道上，墙上已经零零星星贴了好几张，路过的人看了笑笑。环境声：街市人声、孩子的笑声。", vo="人和机器，第一次连到了一起。", music="04_first_light 最亮处", act=A)
shot(8, "verite", "xing amu prop_receipt loc_admin", "In the command hall, Governor Xing in her charcoal uniform slips a folded strip of receipt paper into her breast pocket and gives Amu a small nod, the red lens blurred high behind them.",
     "手持中近景。邢总督把一条折好的纸带放进胸前口袋，朝阿牧微微点头，压低声音说。背景里红色镜头虚虚地亮着。环境声：指挥大厅的键盘声。",
     [("xing", "别让那只眼睛看见。")], music="03_red_lens 回来", act=A)
# ------------------------------------------------------------------ ACT 2
A = "第二幕 · 压顶"
shot(8, "establishing", "loc_jupiter loc_engine", "Wide shot from the ice plain: Jupiter, now enormous, rises behind the planetary engine and fills half the sky, its red spot like an eye, the blue beam looking thin against it.",
     "固定大远景，轻微晃动。巨大的木星从发动机背后升起，占了半个天空，蓝色光柱在它面前显得很细。环境声：越来越低的隆隆声。", vo="木星来了。", music="05_jupiter 低音进入", act=A)
shot(9, "verite", "moss xing loc_admin", "Low angle in the command hall: Governor Xing stands alone facing the huge display wall, the red lens glowing above her.",
     "低机位仰拍。邢总督独自站在屏幕墙前，头顶的红色镜头亮着。平静的合成男声下达指令。环境声：低沉的电子嗡鸣。",
     [("moss", "检测到未授权网络。即刻清除。")], music="03_red_lens", act=A)
shot(9, "verite", "xing loc_admin", "Medium close-up of Governor Xing looking up, jaw set, one hand flat on her breast pocket, consoles behind her going dark.",
     "手持中近景。邢总督抬着头，一只手按在胸前口袋上，一字一句地回答。她身后的操作台一台接一台暗下去。环境声：电子提示音。",
     [("xing", "我不签。这张网救过人。"), ("moss", "总督权限，已暂停。")], music="03_red_lens", act=A)
shot(9, "verite", "loc_hub prop_compute", "Wide handheld shot inside the secret hub in the abandoned pump station: boxy grey automated security units on tracks, each with one red sensor eye, roll in between the improvised racks while the rack lights go out row by row.",
     "手持广角。灰色的自动警戒机一台台开进机房，红色的感应眼扫过机架，机架上的指示灯一排一排地熄灭。环境声：履带声、断电的咔哒声。", vo="MOSS自己动了手。", music="05_jupiter 鼓点", act=A)
shot(10, "verite", "boye loc_hub", "Medium shot at a low steel hatch at the back of the hub: old Boye stands with his back to the hatch he has just closed, hands open at his sides, calm, red sensor light falling across his face.",
     "手持中景。波爷把身后的小铁门关死，转过身，摊开两只手，平静地面对照过来的红光。环境声：铁门的闷响、履带声逼近。",
     [("boye", "你们走。关门的事，我来。")], music="弦乐长音", act=A)
shot(8, "verite", "xiaoman luosi loc_street", "In a pipe alcove off a back alley, Xiaoman throws a grey tarpaulin over the small yellow robot, one finger on his lips, the smiley glow dimming under the cloth.",
     "手持镜头。巷子深处，小满把一块灰色防水布罩在“螺丝”身上，竖起手指贴在嘴上，布底下的笑脸光暗了下去。环境声：远处的履带声、急促的呼吸。", music="弦乐长音", act=A)
shot(8, "establishing", "loc_jupiter", "One single wide landscape image with no people at all: seen from the empty ice plain looking up, Jupiter fills the entire sky, a faint stream of Earth's atmosphere being pulled toward it, the silhouette of the engine tiny on the horizon.",
     "仰拍固定大远景，画面轻微颤动。木星占满整个天空，一缕大气被它吸过去。环境声：极低的隆隆声，像远处的雷。", music="05_jupiter", act=A)
shot(9, "verite", "loc_street", "Handheld shot in the underground street during an earthquake: dust and flakes of rust fall from the pipes, hanging lamps swing wildly, people grab railings and crouch over children.",
     "剧烈晃动的手持镜头。地下城主街在震，灰和锈渣往下掉，吊灯乱甩，人们抓住栏杆，护住孩子蹲下。环境声：轰隆声、尖叫、金属呻吟。", music="05_jupiter 全奏", act=A)
shot(8, "establishing", "loc_engine loc_jupiter", "Wide shot: the planetary engine's blue plasma column sputters, thins and goes out, leaving the black mass of the engine under the orange glow of Jupiter.",
     "固定大远景。发动机的蓝色光柱抖了几下，变细，熄灭。只剩木星的橘红色光压在黑沉沉的发动机上。环境声：轰鸣骤停，只剩风声。", vo="发动机，停了。", music="05_jupiter 骤停", act=A)
shot(10, "verite", "moss loc_admin", "Wide shot of the command hall: the giant display wall going black panel by panel, operators frozen at their consoles, only the red lens still lit high in the middle.",
     "固定广角。屏幕墙一块接一块地黑掉，操作员僵在座位上，只有正中的红色镜头还亮着。平静的合成男声宣布。环境声：一片死寂里的电流声。",
     [("moss", "流浪地球计划已失败。本系统停止地面调度。")], music="无音乐", act=A)
shot(9, "verite", "xing moss loc_admin", "Close-up from below of Governor Xing in the dark hall, lit only red from above, shouting up at the lens.",
     "仰拍特写。黑暗里，邢总督的脸只被头顶的红光照着，她朝着镜头喊，声音在大厅里回荡。镜头没有回答。环境声：回声、远处的哭声。",
     [("xing", "MOSS，回答我。……回答我！")], music="无音乐", act=A)
shot(8, "establishing", "loc_street", "One single image (not a collage, not split panels), no people in the foreground: high angle looking down the huge vertical shaft of the underground city, stacked cabins on the walls, most of their windows already dark, only a few clusters of lit windows left in the blackness.",
     "高机位俯拍。地下城竖井里的灯，一个区接一个区地灭下去，最后几乎全黑。环境声：空旷的风声、遥远的呼喊。", music="无音乐", act=A)
shot(12, "interview", "xing loc_interview", "Interview medium close-up: Governor Xing sits upright in the dim interview room, hands folded, eyes lowered.",
     "采访固定机位。邢总督端坐着，沉默了很久才开口，声音很轻，说完闭了一下眼。环境声：安静的房间底噪。",
     [("xing", "三十万人，都只会跟它说话。它不说话了，我们连彼此在哪儿，都不知道。")], music="02_islands 极弱", act=A)
shot(9, "verite", "xiaoman loc_hub", "In the pitch-dark wrecked hub, lit only by a dropped flashlight on the floor: Xiaoman sits against a fallen rack, knees up, face buried in his arms, shaking.",
     "固定中景。漆黑的机房废墟里，只有掉在地上的手电照着。小满靠着倒下的机架坐着，把脸埋进胳膊里，肩膀在抖。环境声：远处的哭喊、他压着的喘息。", vo="他十九岁，没见过太阳。那一刻，他以为什么都没有了。", music="无音乐", act=A)
shot(9, "macro", "luosi logo_smiley", "Close-up in darkness: under a grey tarpaulin, a red-and-white smiley glow switches on and shines softly through the cloth.",
     "特写固定镜头。黑暗里，防水布底下亮起一团红白色的光，透过布面，显出笑脸的轮廓。环境声：一声轻轻的提示音。", music="07_farewell_luosi 的八音盒动机，极弱", act=A)
shot(9, "verite", "xiaoman luosi loc_hub", "Medium shot in the dark hub: Xiaoman has pulled the tarpaulin off; his tear-streaked face is lit by the glowing smiley screen of the small yellow robot, whose manipulator claw is held out toward him; his hand closes around it.",
     "手持中景。小满扯掉防水布，脸被屏幕上的笑脸照亮。“螺丝”朝他伸着机械爪，他伸手握住，握得很紧。环境声：电机的嗡鸣、吸鼻子的声音。",
     [("xiaoman", "……你还亮着。")], music="八音盒动机 + 大提琴", act=A)
shot(9, "macro", "prop_node logo_smiley", "Close-up along a dusty shelf in the dark hub: one handmade node box blinks a green lamp, then the next one beside it, then a whole row of mismatched boxes lighting up one after another.",
     "特写，沿着货架缓慢横移。一只节点盒的小灯亮了，旁边一只跟着亮，然后一整排大大小小的盒子，一只接一只亮起来。环境声：此起彼伏的提示音。", music="04_first_light 变奏，逐渐展开", act=A)
shot(9, "establishing", "loc_street", "One single image (not a collage), no people in the foreground: high angle looking down the huge black vertical shaft of the underground city, almost everything dark, with dozens of tiny green and white points of light scattered across the darkness like stars.",
     "高机位俯拍。漆黑的竖井里，亮起一个小绿点，又一个，零零星星，越来越多，像有人在黑暗里一盏一盏点灯。环境声：风声里夹着越来越多的提示音。", vo="没有中心。它们一个一个，自己亮了回来。", music="主题进入", act=A)
shot(10, "verite", "xing boye loc_admin", "In a dim holding corridor, Governor Xing turns a heavy manual key in a barred door while old Boye stands inside holding the bars, flashlight light between them.",
     "手持中景。邢总督用一把手动钥匙拧开铁栅门，波爷在里面扶着栏杆看着她。门开了。环境声：钥匙转动的金属声。",
     [("xing", "我来晚了。"), ("boye", "不晚。灯还没灭完。")], music="主题", act=A)
shot(9, "verite", "xiaoman xing prop_node loc_admin", "In the dark command hall under the silent red lens, Xiaoman sets a handmade node box with a smiley sticker on the main console and plugs in a cable, Governor Xing standing beside him pointing at the console.",
     "手持中景。黑着的指挥大厅里，小满把贴着笑脸的铁盒放上主操作台，插上线。邢总督站在旁边下令。头顶的红色镜头沉默地亮着。环境声：插头的咔哒声、脚步声。",
     [("xing", "接进来。全城的眼睛，都接进来。")], music="主题上行", act=A)
shot(9, "establishing", "loc_admin", "Wide shot of the command hall: the giant wall lights up again, not with clean graphics but with a rough hand-fed map made of thousands of small scattered dots, operators rising to their feet.",
     "固定广角。屏幕墙重新亮起，不再是整齐的图表，而是由成千上万个小点拼成的粗糙地图。操作员一个个站了起来。环境声：一片低低的吸气声。", music="主题第一次完整呈现", act=A)
shot(11, "interview", "boye loc_interview", "Interview medium close-up: old Boye in the dim interview room, both hands spread flat as if laying things on a table.",
     "采访固定机位。波爷两只手摊开，像是把东西一样样摆在桌上，慢而笃定地说。环境声：安静的房间底噪。",
     [("boye", "没有谁看得见全部。可每个人看见的那一小块，摆到一张桌上，就是一张图。")], music="主题收", act=A)
# ------------------------------------------------------------------ ACT 3
A = "第三幕 · 饱和"
shot(9, "verite", "jin amu prop_core loc_ice", "Beside a huge truck in blowing snow: Boss Jin and Amu lift a rugged steel case, open for a moment to show the ember-red glowing igniter core, up into the cab.",
     "手持镜头，风雪里。金老板和阿牧合力把一只钢箱抬上驾驶室，箱盖合上前，里面的点火核心泛着暗红的光。环境声：风声、引擎怠速。",
     [("jin", "火石上车。四十公里，冰上走。")], music="06_saturation_rescue 进入", act=A)
shot(8, "verite", "xiaoman luosi loc_ice", "At the tail ramp of a truck in the snow, Xiaoman pushes the small yellow robot with the glowing smiley screen up the ramp, his breath fogging.",
     "手持镜头。小满推着“螺丝”上了车尾的跳板，机器人的履带在冰上打了一下滑，他用肩膀顶住。环境声：履带声、风声。", music="06_saturation_rescue", act=A)
shot(9, "establishing", "loc_ice loc_jupiter", "Wide shot: twelve heavy trucks roll out in a line across the ice plain under the vast orange glow of Jupiter, headlights tiny.",
     "固定大远景。十二台重型运输车排成一线，开进木星的橘红色光里，车灯小得像火星。环境声：引擎的合鸣、风声。", vo="饱和式救援。每一台停机的发动机，都有车队在赶去。", music="06_saturation_rescue", act=A)
shot(9, "verite", "jin prop_node loc_ice", "Inside the shaking cab: the node box on the dashboard flashes its lamps, Boss Jin hauls the wheel hard to the left, orange light through the windscreen.",
     "剧烈晃动的驾驶室内镜头。仪表台上的铁盒急促地闪灯，金老板猛打方向盘向左，整个人被甩得一歪。环境声：急促的提示音、引擎嘶吼。",
     [("jin", "前面裂了！它让我们往左！")], music="06_saturation_rescue", act=A)
shot(8, "establishing", "loc_ice", "Long-lens shot: a crevasse splits the ice behind the convoy and the last truck's headlights tilt, drop and vanish into a cloud of snow.",
     "长焦镜头，晃动。车队后方的冰面裂开，最后一台车的车灯一歪，沉下去，消失在腾起的雪雾里。环境声：冰层断裂的巨响。", music="06_saturation_rescue 骤弱", act=A)
shot(9, "verite", "jin loc_ice", "Tight close-up of Boss Jin gripping a radio handset in the cab, eyes fixed on the mirror, orange light on his scarred cheek.",
     "手持特写。金老板死死攥着对讲机，盯着后视镜，对着话筒喊。对讲机里只有电流声。环境声：电流杂音、引擎声。",
     [("jin", "七号车！老秦！回话！")], music="弦乐长音", act=A)
shot(10, "interview", "jin loc_interview", "Interview medium close-up: Boss Jin sits in the dim interview room, a walking cane across his knees, eyes wet, looking past the lens.",
     "采访固定机位。金老板膝上横着一根拐杖，眼眶是红的，望着镜头外，说得很慢，说完抹了一把脸。环境声：安静的房间底噪。",
     [("jin", "十二台车出去，八台到。老秦没到。")], music="独奏二胡", act=A)
shot(8, "establishing", "loc_engine loc_jupiter", "Wide shot at the foot of the dark, dead planetary engine under Jupiter's glow: a steel relay mast buckles and falls as ice and concrete slide down over a shaft opening.",
     "固定远景，画面震动。停机的发动机脚下，一根中继桅杆折断倒下，冰块和混凝土滑下来，埋住了井口。环境声：坍塌的轰响。", music="低音鼓", act=A)
shot(9, "verite", "amu xiaoman prop_node loc_engine", "At the rubble-choked mouth of a relay shaft: Amu crouches with a node box in his hands, its lamps dark, Xiaoman beside him, wind and snow.",
     "手持镜头。被碎石堵住的井口边，阿牧蹲着，手里的节点盒灯全灭了。他抬头看了一眼发动机，对小满说。环境声：风声、碎石滚落声。",
     [("amu", "中继断了。下面听不见我们。")], music="06_saturation_rescue 低回", act=A)
shot(9, "verite", "luosi xiaoman loc_engine", "Low shot: the small yellow robot with the glowing smiley turns on its tracks to face a narrow black gap between fallen concrete slabs; Xiaoman, behind it, turning his head as he realises.",
     "低机位手持。“螺丝”原地转过身，屏幕对着碎石间一道漆黑的窄缝，停住了。身后的小满慢慢转过头，明白了它要做什么。环境声：电机转动声、风声。", music="八音盒动机", act=A)
shot(9, "verite", "xiaoman luosi loc_engine", "Xiaoman throws both arms around the body of the small yellow robot from behind, heels dug into the ice, shouting.",
     "手持镜头。小满扑上去从后面抱住“螺丝”的机身，脚跟蹬着冰面往回拽，朝它喊。环境声：履带空转的摩擦声、风声。",
     [("xiaoman", "不行！你回来！会压碎的！")], music="八音盒动机 + 弦乐", act=A)
shot(9, "macro", "luosi xiaoman logo_smiley", "Close-up: the robot's glowing smiley screen turned toward Xiaoman's face; its small manipulator claw rests gently on the back of his glove.",
     "特写。“螺丝”停了下来，屏幕转过来对着小满的脸。它抬起机械爪，在他的手套上轻轻碰了一下，然后松开。环境声：电机的轻响，风声忽然远了。", music="八音盒动机，独奏", act=A)
shot(9, "verite", "luosi loc_engine", "From behind: the small yellow robot drives into the narrow dark gap under a tilted concrete slab, its whip antenna scraping the concrete, its glow disappearing inside.",
     "手持镜头，从背后拍。“螺丝”开进了石板底下的窄缝，天线刮着混凝土，身上的光一点点没进黑暗里。环境声：履带声、金属刮擦声。", music="07_farewell_luosi", act=A)
shot(9, "macro", "luosi logo_smiley", "Inside the collapsed shaft, tight shot: the small yellow robot wedged between concrete slabs raises its antenna, dust falling through its smiley glow, a slab pressing down on its roof, a crack running across the screen.",
     "狭小空间里的特写。“螺丝”卡在两块石板中间，把天线一节一节升起来。头顶的石板往下沉，屏幕上裂开一道缝，笑脸还亮着。环境声：混凝土的呻吟、电机吃力的声音。", music="07_farewell_luosi", act=A)
shot(9, "macro", "prop_node amu", "Close-up of the node box in Amu's gloved hands: its lamps come back on, green, one after another, snow blowing across.",
     "特写。阿牧手里的节点盒，灯一颗接一颗重新亮了，绿色。他猛地抬起头喊。环境声：一串急促的提示音、风声。",
     [("amu", "通了！螺丝把自己架成了中继！")], music="06_saturation_rescue 重新起", act=A)
shot(9, "verite", "amu prop_core loc_engine", "Handheld chase shot from behind: Amu, the steel core case on his shoulder, runs down a dark engine gallery lit by emergency lamps.",
     "剧烈晃动的手持跟拍。阿牧扛着钢箱在漆黑的发动机廊道里狂奔，应急灯一盏盏从头顶掠过。环境声：沉重的脚步声、喘息、箱子的碰撞声。", music="06_saturation_rescue 全奏", act=A)
shot(9, "verite", "xiaoman loc_engine", "Xiaoman on his knees at the black gap in the rubble, both hands on the concrete, shouting into the darkness.",
     "手持镜头。小满跪在窄缝前，两只手撑着石板，朝黑洞里喊，声音都劈了。环境声：混凝土的断裂声、风声。",
     [("xiaoman", "撑住！螺丝！再撑一会儿！")], music="06_saturation_rescue", act=A)
shot(8, "macro", "luosi logo_smiley", "Tight shot in the shaft: half of the smiley's pixels are dead, the cracked screen flickering, the antenna still up, dust pouring down.",
     "特写。屏幕上的笑脸灭了一半，剩下的一半在闪。天线还举着。灰不停地往下掉。环境声：电流的噼啪声、石板下沉的闷响。", music="07_farewell_luosi + 鼓", act=A)
shot(9, "macro", "amu prop_core", "Close-up: Amu's gloved hands drive the ember-red glowing igniter core into a steel socket and throw a heavy locking lever.",
     "特写。阿牧把泛着红光的点火核心推进插座，整个人压上去，扳下锁定杆。环境声：金属咬合的巨响、他的嘶吼。", music="06_saturation_rescue 顶点", act=A)
shot(8, "macro", "luosi logo_smiley", "Tight shot in the shaft: the last pixels of the smile flicker once and go out; the cracked screen is dark; dust settles.",
     "特写固定镜头。笑脸最后闪了一下，灭了。屏幕是黑的。灰慢慢落下来。环境声：一切声音都停了，只剩灰落下的沙沙声。", music="全部音乐骤停", act=A)
shot(9, "establishing", "loc_engine loc_jupiter", "Wide shot: the blue-white plasma column of the planetary engine blasts back to life and rises into the Jupiter-filled sky.",
     "固定大远景。发动机底部亮起蓝白色的光，光柱猛地冲上去，刺进木星占满的天空。环境声：从寂静中爆发的轰鸣。", music="08_ignition 的第一个和弦", act=A)
shot(10, "verite", "xiaoman loc_engine", "Close-up of Xiaoman kneeling at the gap, blue light washing over his face from behind; he is not looking at the beam but into the dark gap.",
     "手持特写。蓝光从背后漫过小满的脸。所有人都在欢呼，他没有回头，只盯着那道黑缝，轻轻叫了一声。环境声：远处的欢呼、发动机的轰鸣。",
     [("xiaoman", "螺丝？")], music="07_farewell_luosi 大提琴独自收尾", act=A)
shot(10, "macro", "prop_receipt", "Macro shot: a field printer on a truck tailgate prints a short strip of receipt paper, a small red square stamp at its end, a gloved hand tearing it off, blue light on the snow.",
     "微距特写。车尾板上的打印机吐出一小截纸带，盖上红印。一只戴手套的手把它撕下来，攥在手心。环境声：打印头的哒哒声、远处的轰鸣。", vo="最后一条回执。中继保持：三分五十秒。署名：螺丝。", music="大提琴", act=A)
shot(12, "interview", "xiaoman loc_interview", "Interview close-up: Xiaoman in the dim interview room, the crushed robot head in his lap, crying and smiling at the same time.",
     "采访固定机位，近景。小满抱着压瘪的机器人脑袋，又哭又笑，说到一半停下来吸了口气，才把话说完。环境声：安静的房间底噪。",
     [("xiaoman", "它不会说话。可它那一下，碰了碰我的手。我知道，它是怕的。")], music="无音乐", act=A)
# ------------------------------------------------------------------ ACT 4
A = "第四幕 · 点燃"
shot(9, "verite", "boye loc_admin", "In the relit command hall, old Boye bends over a crackling radio set on the console, headphones on one ear, the rough dot map on the wall behind him.",
     "手持中景。波爷弯腰凑在一台滋滋响的电台前，一只耳朵贴着耳机。电台里传来一个陌生女人沉稳的声音。环境声：电台杂音。",
     [("boye", "发动机回来了。"), ("zhou", "不够。得点燃木星。")], music="08_ignition 心跳鼓", act=A)
shot(9, "verite", "zhou loc_sulawesi", "In the ring-shaped control room at Sulawesi, Researcher Zhou in her white uniform with blue stripes leans on the console holding a radio handset, exhausted, the tilted steering engine visible through the window.",
     "手持中景。苏拉威西控制室里，周研究员撑着操作台，握着话筒，嗓子是哑的。窗外是倾斜的转向发动机。环境声：警报的低鸣、电台杂音。",
     [("zhou", "我们缺冷却液，缺人手。谁有？")], music="08_ignition 心跳鼓", act=A)
shot(9, "verite", "xing prop_receipt loc_admin", "Close shot at a console: Governor Xing signs a strip of receipt paper with a pen, her other hand holding it flat, operators watching.",
     "手持近景。邢总督把一条纸带按在操作台上，提笔签了字，头也没抬地说。周围的操作员都看着她。环境声：笔尖声、电台杂音。",
     [("xing", "敦煌给。全城降四度。我签。")], music="08_ignition 弦乐进", act=A)
shot(9, "verite", "loc_ice logo_smiley", "On the ice at a meeting point: crews from different convoys in mismatched suits pass coolant canisters from truck to truck in a chain, a boxy loader robot in the middle of the line taking a canister from a human's hands with its claw; smiley stickers on the truck doors.",
     "手持镜头。冰原上，几支素不相识的车队碰了头，人排成一列传递冷却罐，队伍中间夹着一台装卸机器人，机械爪从人手里接过罐子，再递给下一个人。环境声：风声、金属罐的碰撞声、吆喝声。", vo="素不相识的人。素不相识的机器。", music="08_ignition 渐强", act=A)
shot(8, "macro", "loc_sulawesi", "Macro shot: a gloved human hand and a steel robot manipulator grip the same frozen valve wheel and turn it together, frost cracking off.",
     "微距特写。一只戴手套的人手和一只钢制机械爪握在同一个结冰的阀轮上，一起用力，冰霜崩裂，阀轮转动。环境声：冰裂声、金属转动声。", music="08_ignition 渐强", act=A)
shot(9, "establishing", "loc_sulawesi", "Wide shot over a frozen sea: the colossal tilted steering engine fires its blue beam at full power toward Jupiter, the light bleaching the ice.",
     "固定大远景。冰封的海面上，倾斜的转向发动机全功率喷射，蓝色光柱直指木星，把冰面照得发白。环境声：撕裂般的轰鸣。", music="08_ignition 渐强", act=A)
shot(10, "establishing", "loc_jupiter", "From the ice plain looking up: a silent white-orange flash blooms on the face of Jupiter and spreads across the whole sky.",
     "仰拍固定大远景。木星表面绽开一团白光，无声地铺满整个天空，雪地被照成一片白。环境声：绝对的寂静，几秒后才传来低沉的闷响。", music="08_ignition 顶点和弦，然后寂静", act=A)
shot(10, "verite", "amu xiaoman jin loc_ice", "On the ice: Amu, Xiaoman and Boss Jin leaning on a cane stand among other crew, faces lit white, looking up without a word; beside them a small loader robot has tilted its sensor head up as well.",
     "手持镜头，缓慢横摇。冰面上，阿牧、小满、拄着拐的金老板和其他人，脸被照得雪白，仰着头，谁也没说话。他们身边，一台小机器人也把感应头仰了起来。环境声：风声，没有人声。", music="08_ignition 余韵弦乐", act=A)
shot(9, "establishing", "loc_engine", "Wide shot of the ice plain: several engine beams burning on the horizon, the burning disc of Jupiter visibly smaller behind them.",
     "固定大远景。地平线上，几道发动机的光柱稳稳地亮着，燃烧的木星在它们背后，一点一点变小。环境声：平稳的轰鸣、风声。", vo="地球，开始离开。", music="09_belongs_to_everyone 进入", act=A)
# ------------------------------------------------------------------ CODA
A = "尾声 · 属于所有人"
shot(9, "verite", "moss amu loc_admin", "In the quiet command hall, Amu stands alone looking up at the red lens, the rough dot map glowing on the wall beside it.",
     "固定中景。安静下来的指挥大厅里，阿牧独自站着，抬头看着红色镜头。平静的合成男声开口，他答了一句。环境声：屏幕的低鸣。",
     [("moss", "你们选择了低效的方式。"), ("amu", "我们选择了彼此。")], music="无音乐", act=A)
shot(8, "macro", "moss", "Extreme close-up of the red lens: in the black glass, the small reflection of Amu turning and walking away; the lens does not change.",
     "大特写固定镜头。红色镜头的玻璃上，阿牧的倒影转身，越走越小。镜头没有回答。环境声：轻微的电流声。", music="无音乐", act=A)
shot(10, "interview", "amu loc_interview", "Interview medium close-up: Amu in the dim interview room, calm, looking straight at the interviewer.",
     "采访固定机位。阿牧看着采访者，平静地说，说完没有再补充。环境声：安静的房间底噪。",
     [("amu", "规则不属于任何一个人，所以，才属于所有人。")], music="09_belongs_to_everyone", act=A)
shot(10, "verite", "loc_street prop_receipt", "A long corridor in the underground city turned into a memorial: thousands of receipt paper strips pinned to the wall like prayer slips, stirring in the ventilation; people stand before them, a child touches one strip, a small maintenance robot waits beside the child.",
     "手持镜头，缓慢前移。一条长走廊的墙上，钉满了成千上万条回执纸带，被通风口的风吹得轻轻翻动。人们站在墙前，一个孩子伸手摸了摸其中一条，旁边停着一台小维修机器人。环境声：纸带的沙沙声、低声的交谈。", vo="每一份付出都被记住了。人的，和机器的。", music="09_belongs_to_everyone", act=A)
shot(9, "verite", "xiaoman boye loc_stall", "In the repair stall under the warm lamp: Xiaoman solders inside the open, dented body of the small yellow robot, its cracked screen dark; old Boye holds a work lamp for him.",
     "手持中景。修理铺的台灯下，小满埋头在“螺丝”被压瘪的机身里焊线，屏幕是裂的、黑的。波爷在旁边替他举着灯。环境声：电烙铁的滋滋声。", music="07_farewell_luosi 八音盒动机回来", act=A)
shot(9, "macro", "luosi logo_smiley", "Close-up of the robot's cracked square screen: it flickers twice and the red-and-white smiley lights up again, a crack running across the smile.",
     "特写固定镜头。裂了一道缝的屏幕闪了两下，笑脸重新亮了起来，裂缝正好横在笑容上。环境声：一声熟悉的开机提示音。", music="八音盒动机完整奏完", act=A)
shot(10, "verite", "xiaoman luosi loc_stall", "Medium shot at floor level: Xiaoman, laughing through tears, holds out his open hand; the dented yellow robot with the cracked glowing smiley raises its manipulator claw and touches his palm.",
     "手持低机位中景。小满又哭又笑，蹲下来伸出手掌。“螺丝”抬起机械爪，碰了碰他的手心，和第一次一样。环境声：电机声、他的笑声。",
     [("xiaoman", "欢迎回家，螺丝。")], music="主题温暖再现", act=A)
shot(13, "interview", "boye loc_interview", "Interview medium close-up: old Boye in the dim interview room, glasses on, a small stubborn smile, looking straight at the interviewer.",
     "采访固定机位。波爷扶了扶眼镜，看着采访者，一句一句慢慢地说，说完笑了一下。环境声：安静的房间底噪。",
     [("boye", "勇气不是不怕。是怕，还把手伸出去。人类的赞歌，就是勇气的赞歌。连一台小机器，都懂。")], music="主题", act=A)
shot(10, "establishing", "loc_engine prop_node logo_smiley", "Final shot from inside a cabin window: on the sill a small handmade node box with a smiley sticker blinks a green lamp; beyond the glass, the ice plain, the engine beams, and Jupiter shrunk to a bright point.",
     "固定镜头，极缓慢推近。窗台上，一只贴着笑脸的小铁盒一下一下闪着绿灯。窗外是冰原、发动机的光柱，和已经缩成一个亮点的木星。环境声：平稳的轰鸣，小灯的提示音。", vo="路还有两千五百年。灯还亮着。", music="主题歌《未熄》起", act=A)

json.dump({"episode": 13, "title": "未熄（短片）", "concept": "人类的赞歌是勇气的赞歌；ANET 是具身智能与人类智能的团结。",
           "logline": "MOSS 判了地球死刑并沉默。一个没见过太阳的少年、一台报废的维修机器人，和一群凡人，把手伸向了彼此。",
           "shots": S}, open(os.path.join(ROOT, "series", "ep13.json"), "w"), ensure_ascii=False, indent=1)
tot = sum(s["dur"] for s in S)
bad = [(s["id"], sum(len(d["line"]) for d in s["dialogue"]), s["dur"]) for s in S if sum(len(d["line"]) for d in s["dialogue"]) > 3.6 * s["dur"]]
print(len(S), "shots", tot, "s =", round(tot / 60, 1), "min; over-long dialogue:", bad)

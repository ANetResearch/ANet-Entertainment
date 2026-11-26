#!/usr/bin/env python3
"""Reference-image registry (characters / locations / props). Writes refs/refs.json + refs/jobs.json."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE = ("Documentary still photograph, shot on a 35mm cinema camera in available light, natural film grain, "
         "muted cold palette with a few warm practical lamps, unposed and observational, photorealistic, "
         "near-future hard science fiction, worn and lived-in. No captions, no subtitles, no watermark, no legible text anywhere.")
PORTRAIT = "Waist-up environmental portrait, eye level, subject looking slightly off camera, shallow depth of field, plain blurred background of an underground concrete corridor. "
SMILEY = "assets/logos/anet-smiley.png"
WORD = "assets/logos/agent-network-logo.png"
ADL = "assets/logos/autodl-logo.png"
R = [
 # ---- characters
 dict(id="amu", kind="character", zh="阿牧，34岁男性，行星发动机通信维护工程师，黑色短发有些凌乱，左眉有一道旧疤，下巴有胡茬，穿磨旧的橙灰色保温工装，胸前挂工具包",
      prompt=PORTRAIT + "A 34-year-old Chinese man, communications maintenance engineer for a planetary engine. Short messy black hair, a thin old scar through his left eyebrow, light stubble, lean face, tired intelligent eyes. Worn orange-and-grey insulated work coverall with scuffed reflective strips, a small canvas tool pouch strapped across his chest, fingerless thermal gloves."),
 dict(id="boye", kind="character", zh="波爷，61岁男性，旧互联网协议工程师，灰白短须，戴用胶布缠过镜腿的黑框眼镜，穿深蓝色旧棉袄",
      prompt=PORTRAIT + "A 61-year-old Chinese man, retired network protocol engineer who now runs a repair stall. Short grey-white beard, thinning grey hair, black-framed glasses with one temple wrapped in tape, deep wrinkles, gentle stubborn expression. Faded dark navy quilted cotton jacket over a brown knitted vest, a soldering-stained apron."),
 dict(id="xiaoman", kind="character", zh="陈小满，19岁男性，地下城出生的学徒，瘦高，乱蓬蓬的头发，脖子上挂着一副大号旧耳机，穿过大的军绿色夹克",
      prompt=PORTRAIT + "A 19-year-old Chinese young man born in an underground city, apprentice technician. Tall and thin, messy overgrown black hair, pale skin that has never seen the sun, quick curious eyes, an oversized battered pair of headphones hanging around his neck. Oversized olive-green field jacket with rolled sleeves and many pockets full of wires."),
 dict(id="jin", kind="character", zh="金老板，45岁男性，地表运输车队的老板兼队长，宽脸，络腮短胡，脸颊有冻伤疤痕，穿厚重的黑色地表防寒服，毛领敞开",
      prompt=PORTRAIT + "A 45-year-old man, boss and captain of a surface heavy-transport convoy. Broad weathered face, short full beard with frost-grey patches, old frostbite scars on both cheeks, heavy build. Bulky black insulated surface exosuit undersuit with the fur-lined collar open, helmet clipped at his hip, thick gloves tucked in belt."),
 dict(id="xing", kind="character", zh="邢总督，50岁女性，地下城总督，灰白头发整齐盘起，穿笔挺的深灰色联合政府制服，神情克制",
      prompt=PORTRAIT + "A 50-year-old Chinese woman, chief administrator of an underground city. Grey-streaked hair in a tight neat bun, sharp cheekbones, composed and guarded expression, straight posture. Crisp dark charcoal government uniform jacket with a high collar and a plain unmarked metal pin, a slim tablet held against her chest."),
 dict(id="zhou", kind="character", zh="周研究员，38岁华人女性，苏拉威西转向发动机的驻站研究员，齐肩黑发扎成低马尾，戴细框眼镜，穿白色带蓝条的发动机控制室制服，耳后别着一支笔",
      prompt=PORTRAIT + "A 38-year-old Chinese woman, resident researcher at an equatorial steering-engine control station. Shoulder-length black hair tied in a low ponytail, thin wire-framed glasses, calm focused eyes, a pencil tucked behind her ear. White technical uniform jacket with blue shoulder stripes, sleeves pushed up, a lanyard with a blank badge. Background: blurred control room with cold blue monitors."),
 dict(id="luosi", kind="character", inputs=[SMILEY], zh="“螺丝”，一台膝盖高的旧式履带维修机器人，掉漆的黄色外壳，头部是一块小黑屏，屏幕上亮着红白色的ANET笑脸标志",
      prompt="A small knee-high tracked maintenance robot standing on a wet concrete floor of an underground corridor, full body, three-quarter view. Boxy scratched yellow steel body with chipped paint and hand-welded patches, two rubber tracks, one folded manipulator arm, a short whip antenna. Its head is a small square black screen that displays exactly the smiley speech-bubble logo from the reference image (red rounded speech bubble outline, red connected node squares, white smile) glowing softly. " ),
 dict(id="moss", kind="character", zh="MOSS终端：嵌在金属墙面里的黑色监控终端，中央一枚发红光的圆形镜头",
      prompt="Close view of an artificial-intelligence monitoring terminal built into a brushed-steel wall panel of a control hall: a black glass housing with a single round camera lens glowing deep red in its centre, a thin ring of red light around it, faint reflections of people in the glass. Cold, clinical, perfectly clean in contrast with the worn surroundings. "),
 # ---- locations
 dict(id="loc_street", kind="location", zh="地下城主街：层层叠叠的钢结构居住舱、管道与昏黄灯光，人群拥挤，蒸汽弥漫",
      prompt="Wide shot of the main street of a huge underground city five kilometres below the surface: stacked steel habitation modules on both sides, exposed pipes and cable trays overhead, steam vents, food stalls with warm bulbs, crowds of ordinary people in padded work clothes, puddles on the concrete floor, haze in the air. "),
 dict(id="loc_comms", kind="location", zh="通信维护舱：狭窄的机柜间，成排的旧服务器机柜、缠绕的线缆、一张堆满仪器的工作台",
      prompt="Interior of a cramped communications maintenance bay inside a planetary-engine complex: rows of old server racks with small status lights, thick bundles of cables, a steel workbench crowded with oscilloscopes and handheld diagnostic terminals whose screens show only abstract waveforms, a thermos, frost on a ventilation grille. Empty of people. "),
 dict(id="loc_stall", kind="location", zh="波爷的修理铺：地下城巷子里的小铺子，堆满旧路由器、显像管显示器、电烙铁和线圈，一盏暖黄台灯",
      prompt="Interior of a tiny electronics repair stall in an alley of an underground city: shelves overflowing with old routers, CRT monitors, radio parts, coils of wire, a soldering station under a single warm desk lamp, a kettle, a faded photograph pinned to the wall, a roll-up steel shutter half open. Empty of people. "),
 dict(id="loc_engine", kind="location", zh="行星发动机外景：冰封平原上矗立的山一样巨大的行星发动机，喷出冲天的蓝白色等离子光柱",
      prompt="Extreme wide exterior shot on the frozen surface of the Earth: a planetary engine the size of a mountain rises from an ice plain, a colossal industrial structure of steel and concrete, firing a blinding blue-white plasma column straight up into a black starry sky. Tiny lights of vehicles at its base give the scale, blowing snow, minus eighty degrees. "),
 dict(id="loc_ice", kind="location", zh="冰原与车队：冰封的城市废墟之间，一列重型运输车亮着车灯在风雪中行驶",
      prompt="Wide exterior shot of a convoy of massive heavy-haul transport trucks with huge wheels driving across a frozen plain between the ice-encased ruins of skyscrapers, headlights cutting through blowing snow, dark sky, a faint blue glow of a distant engine beam on the horizon. "),
 dict(id="loc_admin", kind="location", zh="地下城行政指挥中心：阶梯式控制大厅，成排的操作台，正面墙上是巨大的暗色屏幕和一枚红色镜头",
      prompt="Interior of the administration command centre of an underground city: a tiered control hall with rows of consoles and operators seen from behind, a giant dark display wall showing only abstract maps and graphs, and high in the middle of the wall a single round red-glowing camera lens of the central AI. Cold blue-white light. "),
 dict(id="loc_interview", kind="location", zh="采访间：昏暗的混凝土房间，一把金属椅子，一盏柔光灯从侧面打来，背景是虚化的管道",
      prompt="An oral-history interview set in a dim concrete room: one plain metal chair facing the camera, a single soft key light from the left, out-of-focus pipes and a small warm lamp in the background, a boom microphone tip at the top edge of frame. Empty chair, no people. "),
 dict(id="loc_sulawesi", kind="location", zh="苏拉威西转向发动机控制室：环形控制室，巨大的观察窗外是冰封的海面和倾斜的转向发动机光柱",
      prompt="Interior of the control room of an equatorial steering engine in Sulawesi: a ring of consoles with cold blue monitors showing abstract gauges, a huge observation window beyond which lies a frozen sea and a tilted colossal engine nozzle firing a blue plasma beam at an angle into the sky. A few operators in white uniforms seen from behind. "),
 dict(id="loc_hub", kind="location", inputs=[WORD], zh="ANET秘密机房：废弃泵站里的自建机房，旧设备拼成的节点架，一只木箱上喷着Agent Network的红黑字标",
      prompt="Interior of a secret self-built network hub inside an abandoned pump station of an underground city: improvised racks made of scaffolding holding dozens of mismatched salvaged computers, radios and robot controllers linked by hand-crimped cables, small red and white indicator lights, a tarp roof, work lamps. In the foreground a wooden equipment crate carries a clean stencilled copy of the black-and-white wordmark logo from the reference image, reproduced exactly. Empty of people. "),
 dict(id="loc_jupiter", kind="location", zh="木星压顶的冰原：木星和大红斑占满整个天空，冰原被染成暗橙色",
      prompt="Exterior wide shot from the frozen surface of the Earth looking up: the planet Jupiter fills almost the entire sky, its bands and the Great Red Spot terrifyingly close, staining the ice plain dull orange; a faint stream of atmosphere is being pulled from the Earth towards it; silhouettes of a stalled planetary engine and a tiny transport truck on the horizon. "),
 # ---- props
 dict(id="prop_node", kind="prop", inputs=[SMILEY], zh="ANET节点盒：用旧弹药铁盒和回收电路板手工做的节点设备，带一根短天线，盒盖上贴着ANET笑脸贴纸",
      prompt="Close-up product-less documentary photo of a handmade network node device on a workbench: an old dented steel ammunition tin fitted with a salvaged circuit board, a small heat sink, three tiny indicator LEDs (two red, one white) and a short screw-on antenna. On its lid is a slightly worn sticker that reproduces exactly the smiley speech-bubble logo from the reference image. Solder wire and a multimeter beside it. "),
 dict(id="prop_receipt", kind="prop", zh="回执纸带：从小型热敏打印机里吐出的长纸带，上面是成排的条形码样校验纹，纸带末端盖着一枚红色小印",
      prompt="Close-up of a long strip of thermal paper curling out of a small battered field printer held in gloved hands: the strip is covered with rows of abstract barcode-like verification marks and dot matrices (no readable letters), and near its end a small red square stamp mark. Shallow depth of field. "),
 dict(id="prop_core", kind="prop", zh="火石：装在钢制防震手提箱里的发动机点火核心，一根泛着暗红光的柱体",
      prompt="Close-up of an engine igniter core resting in the foam cradle of an open rugged steel carrying case inside a truck cabin: a forearm-length metal cylinder with a translucent section glowing deep ember red, frost on the case latches, a gloved hand on the lid. "),
 dict(id="prop_compute", kind="prop", inputs=[ADL], zh="AutoDL算力箱：回收来的GPU算力机箱，灰色金属外壳，侧面有一枚蓝色三叶旋涡形的AutoDL标志，风扇转动，指示灯闪烁",
      prompt="Documentary close view of a salvaged GPU compute server chassis sitting on a scaffolding shelf in an improvised machine room: a scuffed grey steel rack unit with ventilation grilles, spinning fans, a row of small green and white status lights, thick power cables. On its side panel is a clean enamel badge that reproduces exactly the blue three-bladed triangular swirl logo from the reference image. Work lamp light, dust. "),
]
EN = {
 "amu": ("Amu (34, male communications engineer, the protagonist)", "the protagonist"),
 "boye": ("Boye, 'Grandpa Bo' (61, male, old network protocol engineer)", "the mentor"),
 "xiaoman": ("Xiaoman (19, male apprentice)", "the apprentice"),
 "jin": ("Boss Jin (45, male, surface convoy boss)", "the convoy boss"),
 "xing": ("Governor Xing (50, female, governor of the underground city)", "the city governor"),
 "zhou": ("Researcher Zhou (38, female, resident researcher at the Sulawesi steering engine)", "the remote ally"),
 "luosi": ("Luosi, 'Screw' (small yellow tracked maintenance robot with the ANET smiley on its screen face)", "the robot character; it never speaks"),
 "moss": ("MOSS terminal (black AI terminal with one red glowing lens)", "the central AI's physical presence"),
 "loc_street": ("the underground city main street", "location reference"),
 "loc_comms": ("the communications maintenance bay", "location reference"),
 "loc_stall": ("Boye's electronics repair stall", "location reference"),
 "loc_engine": ("the planetary engine exterior on the ice plain", "location reference"),
 "loc_ice": ("the frozen plain with the heavy-truck convoy", "location reference"),
 "loc_admin": ("the administration command hall", "location reference"),
 "loc_interview": ("the oral-history interview room", "location reference"),
 "loc_sulawesi": ("the Sulawesi steering-engine control room", "location reference"),
 "loc_hub": ("the secret ANET hub in an abandoned pump station", "location reference"),
 "loc_jupiter": ("the ice plain under a sky filled by Jupiter", "location reference"),
 "prop_node": ("the handmade ANET node box with the smiley sticker", "prop reference"),
 "prop_receipt": ("the receipt paper strip from a field printer", "prop reference"),
 "prop_core": ("the engine igniter core in its steel case", "prop reference"),
 "prop_compute": ("the salvaged AutoDL GPU compute chassis with the blue three-bladed swirl badge", "prop reference"),
}
reg, jobs = {}, []
for r in R:
    sub = {"character": "characters", "location": "locations", "prop": "props"}[r["kind"]]
    out = f"refs/{sub}/{r['id']}.png"
    reg[r["id"]] = {"kind": r["kind"], "file": out, "zh": r["zh"], "en_name": EN[r["id"]][0], "role": EN[r["id"]][1],
                    "en": r["prompt"].replace(PORTRAIT, "").strip()}
    jobs.append({"id": r["id"], "out": out, "prompt": r["prompt"] + STYLE, "inputs": r.get("inputs", [])})
reg["logo_smiley"] = {"kind": "logo", "file": SMILEY, "zh": "ANET笑脸标志：红色对话气泡外框、红色节点连线和白色笑脸", "en_name": "the ANET smiley logo", "role": "in-world logo reference", "en": "A red rounded speech-bubble outline containing red connected node squares and a white smile, on black. Reproduce its shape exactly wherever it appears on a screen, sticker or painted surface."}
reg["logo_word"] = {"kind": "logo", "file": WORD, "zh": "Agent Network 红黑字标", "en_name": "the Agent Network wordmark", "role": "in-world logo reference", "en": "A red-and-black horizontal wordmark plate. Reproduce it exactly where it is stencilled on a crate or equipment case."}
reg["logo_autodl"] = {"kind": "logo", "file": ADL, "zh": "AutoDL标志：蓝色三叶旋涡形图标", "en_name": "the AutoDL logo", "role": "in-world logo reference", "en": "A blue three-bladed triangular swirl icon. Reproduce it exactly as an enamel badge on compute hardware."}
json.dump(reg, open(os.path.join(ROOT, "refs/refs.json"), "w"), ensure_ascii=False, indent=1)
json.dump(jobs, open(os.path.join(ROOT, "refs/jobs.json"), "w"), ensure_ascii=False, indent=1)
print(len(jobs), "ref jobs")

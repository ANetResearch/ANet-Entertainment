#!/usr/bin/env python3
"""Generate the score with Lyria 3 on gravitex.  usage: gen_music.py [--only id,id] [--workers 4]
Outputs music/<id>.mp3 + music/<id>.txt (prompt and returned lyrics/structure)."""
import base64, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "tools", "config.json")))["gravitex"]
H = {"Authorization": "Bearer " + CFG["key"], "Content-Type": "application/json"}
COMMON = " Original composition, no imitation of any existing artist, film score or melody. High fidelity cinematic production."
WEIXI = """[Verse 1]
冰封了海 也封了来时的路
一万座灯 各自亮在深处
我们都只对着同一个方向说话
却听不见 隔壁的呼吸
[Pre-Chorus]
直到那一夜 天空压下来
直到那个声音 说它不再回答
[Chorus]
那就把手给我 把名字给我
把你看见的那一小块 交给我
没有谁是光 我们只是不肯熄
一盏接着一盏 亮到天明
[Verse 2]
它没有心跳 只有一颗旧螺丝
替我们走进 最黑的那口井
三分五十秒 够一颗星重新点燃
它的笑脸 留在风雪里
[Bridge]
不是神明 不是奇迹
是凡人 是铁 是彼此
[Final Chorus]
那就把手给我 把勇气给我
地球很小 装得下每一个名字
没有谁是光 我们只是不肯熄
我们不肯熄 我们不曾熄"""
ZANGE = """[Verse 1]
当太阳老去 我们没有跪下
当大地冻裂 我们向下安家
当木星遮住了整片天空
我们点起了 一万支火把
[Chorus]
人类的赞歌 是勇气的赞歌
不问归期 不问代价
铁做的手 牵着血肉的手
一步一步 把家推向远方
[Verse 2]
记住每一个 没有回来的名字
记住每一台 不会说话的机器
规则不属于任何一个人
所以它属于 我们每一个
[Chorus]
人类的赞歌 是勇气的赞歌
不问归期 不问代价
铁做的手 牵着血肉的手
一步一步 把家推向远方
[Outro]
两千五百年 路还很长
灯还亮着 我们还在路上"""
LUOSI = """[Verse 1]
你是我从废料堆里捡回来的
一身黄漆 掉了一半
我在你脸上画了一个笑
你就一直 笑到现在
[Chorus]
小螺丝 小螺丝
拧紧了 就不要怕
这个世界很大很冷
可你亮着 我就看得见家
[Verse 2]
那天你自己开进了井里
没回头 也没说话
我把你的笑脸重新点亮
你看 天快亮了
[Outro]
小螺丝 小螺丝
我们回家"""
T = [
 ("01_main_theme_a", "Create a 3-minute instrumental main theme for a documentary-style science fiction film about humanity saving a frozen Earth. Elegiac, tragic-heroic and epic: begin with a lone erhu and a solo cello over a cold low drone, add a wordless low male choir humming, then slowly build with full string orchestra, French horns and distant taiko drums to a noble, sorrowful, hymn-like climax, and end quietly on the solo cello. 60 BPM, D minor resolving to D major in the last bars. Instrumental only, no lyrics."),
 ("01_main_theme_b", "Create a 3-minute instrumental main theme, an elegy for humankind that turns into a hymn of courage. Solo piano states a simple eight-note motif, joined by a guzheng and a solo violin, then a wordless mixed choir and full symphony orchestra carry the motif to a vast, solemn, heroic statement with timpani and brass, before falling back to the lone piano. 56 BPM, C minor. Instrumental only, no lyrics, wordless choir allowed."),
 ("02_islands", "Create a 2-minute instrumental cue: loneliness inside a vast underground city. Sparse felt piano, guzheng harmonics, bowed glass, a very quiet cold synth drone, long silences between phrases. Melancholic, intimate, restrained. 50 BPM, A minor. Instrumental only, no drums."),
 ("03_red_lens", "Create a 2-minute instrumental suspense cue for a calm, polite, all-seeing artificial intelligence. Slow pulsing low analogue synth, a ticking clock-like motif on muted strings, cold high sustained tones, rising quiet unease with no release. 70 BPM, minimal, clinical. Instrumental only."),
 ("04_first_light", "Create a 2-minute instrumental cue of fragile hope: small handmade machines finding each other in the dark. Warm pizzicato strings, kalimba and celesta like tiny blinking lights, a gentle clarinet melody, slowly joined by soft strings. Tender, curious, quietly brave. 84 BPM, F major. Instrumental only."),
 ("05_jupiter", "Create a 2.5-minute instrumental disaster cue: a giant planet fills the sky and the engines of the Earth fail. Massive low brass clusters, pounding taiko and bass drum, tolling tubular bells, a wordless choir crying out, strings in frantic tremolo, then a sudden collapse into a hollow silence with one distant bell. Terrifying, monumental, tragic. 100 BPM, E-flat minor. Instrumental only."),
 ("06_saturation_rescue", "Create a 3-minute instrumental cue for a desperate convoy crossing an ice plain to save a city: relentless driving string ostinato, snare and taiko march, heroic but grieving horn theme, a solo erhu crying above the orchestra, building wave after wave to a blazing climax. Tragic-heroic, unstoppable. 120 BPM, D minor. Instrumental only."),
 ("07_farewell_luosi", "Create a 2.5-minute instrumental lament for a small brave robot that sacrifices itself: a simple music-box melody, answered by a solo cello, then a hushed string choir; the music-box melody slows and stops unfinished, and the cello finishes the phrase alone. Heartbreaking, tender, dignified. 54 BPM, G minor. Instrumental only."),
 ("08_ignition", "Create a 2.5-minute instrumental climax: all of humanity acting together at the last second. Starts with a single held note and a heartbeat drum, then full orchestra and wordless choir rise in an enormous slow crescendo, bells, organ and brass, a blinding triumphant chord, followed by sixty seconds of awed, quiet strings. Sublime, overwhelming, cathartic. 66 BPM, D major. Instrumental only."),
 ("09_belongs_to_everyone", "Create a 2.5-minute instrumental closing cue: dawn after the catastrophe, ordinary people rebuilding. The main elegiac theme returns warm and unhurried on acoustic guitar and piano, then gentle strings and a children's wordless choir, ending with hope rather than triumph. 72 BPM, D major. Instrumental only."),
 ("10_song_weixi_a", "Create a 3.5-minute theme song sung in Mandarin Chinese by a clear, restrained female voice, joined by a mixed choir in the bridge and final chorus. Cinematic ballad that grows from solo piano and cello into full orchestra with taiko: elegiac, tragic-heroic, an anthem of courage. 62 BPM, D minor to D major. Sing exactly these lyrics:\n" + WEIXI),
 ("10_song_weixi_b", "Create a 3.5-minute theme song sung in Mandarin Chinese by a warm, weathered male voice with a female harmony, a full choir entering at the bridge. Starts almost a cappella with a single guitar, grows into an epic orchestral anthem with drums and strings: sorrowful, proud, deeply human. 64 BPM. Sing exactly these lyrics:\n" + WEIXI),
 ("11_song_hymn_of_courage_a", "Create a 3-minute choral anthem sung in Mandarin Chinese by a large mixed choir with full symphony orchestra, slow solemn march tempo, like a requiem that becomes a hymn: tragic, majestic, epic, deeply moving, with timpani, brass and organ in the final chorus. 60 BPM, C minor to C major. Sing exactly these lyrics:\n" + ZANGE),
 ("11_song_hymn_of_courage_b", "Create a 3-minute anthem sung in Mandarin Chinese: first verse by a solo boy soprano with strings, chorus by a full mixed choir and orchestra, second verse by a low male choir, final chorus by everyone with taiko drums and brass. An elegy for humankind and a hymn to courage, solemn and epic. 58 BPM. Sing exactly these lyrics:\n" + ZANGE),
 ("12_song_luosi", "Create a 2.5-minute gentle end-credits ballad sung in Mandarin Chinese by a young male voice, intimate and sincere, with acoustic guitar, a small music-box motif and soft strings; tender, bittersweet, a lullaby for a little robot. 76 BPM, G major. Sing exactly these lyrics:\n" + LUOSI),
]

def one(item):
    tid, prompt = item
    out = os.path.join(ROOT, "music", tid + ".mp3")
    if os.path.exists(out):
        return tid, "skip"
    err = ""
    for attempt in range(3):
        try:
            r = requests.post(CFG["url"] + "/v1beta/interactions", headers=H, timeout=120,
                              json={"model": "lyria-3-pro-preview", "input": prompt + COMMON, "background": True, "store": True}).json()
            iid = r.get("id")
            if not iid:
                err = json.dumps(r, ensure_ascii=False)[:300]; time.sleep(10); continue
            t0 = time.time()
            while time.time() - t0 < 1200:
                time.sleep(6)
                d = requests.get(CFG["url"] + "/v1beta/interactions/" + iid, headers=H, timeout=120).json()
                if d.get("status") == "completed":
                    open(out, "wb").write(base64.b64decode(d["output_audio"]["data"]))
                    open(out[:-4] + ".txt", "w").write("PROMPT\n" + prompt + COMMON + "\n\nMODEL OUTPUT TEXT\n" + str(d.get("output_text", "")) + "\n")
                    return tid, f"ok {os.path.getsize(out)//1024}KB {int(time.time()-t0)}s"
                if d.get("status") in ("failed", "cancelled"):
                    err = json.dumps(d.get("error"), ensure_ascii=False)[:300]; break
        except Exception as e:
            err = repr(e)[:300]; time.sleep(10)
    return tid, "FAIL " + err

if __name__ == "__main__":
    only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    todo = [t for t in T if not only or t[0] in only]
    with ThreadPoolExecutor(workers) as ex:
        for tid, st in ex.map(one, todo):
            print(time.strftime("%T"), tid, st, flush=True)

"""
s2_endcard.py ― 書き出した動画の最後に「絵文字2択のコメント誘導カード」を重ねる（コメントを増やすため）
  python3 s2_endcard.py in.mp4 out.mp4 START "問い" "🗑️" "消す" "📷" "消さない" "▶ 次回テキスト" [HOLD]
  START 秒から画面を暗くして、問い・大きな絵文字2つ・「絵文字ひとつでコメントしてね👇」を出す。最後のコマを HOLD 秒のばす。
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

def emoji_png(ch, path, size=150):
    f = ImageFont.truetype(EMOJI_FONT, 109)                       # カラー絵文字フォントは 109px 固定
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    im.save(path)

def ass_text(path, q, la, lb, nxt, t0, t1):
    def ts(s):
        return "%d:%02d:%05.2f" % (s // 3600, s % 3600 // 60, s % 60)
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: q,IPAPGothic,54,&H0000E5FF,&H0000E5FF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,5,0,5,20,20,0,1
Style: l,IPAPGothic,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,4,0,5,0,0,0,1
Style: s,IPAPGothic,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,3,0,5,0,0,0,1
Style: box,IPAPGothic,20,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def rr(x0, y0, x1, y1, r):
        k = 0.45 * r
        return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
                % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
                   x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))
    a, b = ts(t0), ts(t1)
    ev = [
        "Dialogue: 0,%s,%s,box,,0,0,0,,{\\an7\\pos(0,0)\\p1\\1c&H000000&\\1a&H0C&\\fad(250,0)}%s{\\p0}" % (a, b, rr(-10, -10, 730, 1290, 0)),
        "Dialogue: 1,%s,%s,q,,0,0,0,,{\\an5\\pos(360,330)\\fad(200,0)}%s" % (a, b, q),
        "Dialogue: 1,%s,%s,box,,0,0,0,,{\\an7\\pos(0,0)\\p1\\1c&HFFFFFF&\\1a&HD8&\\bord3\\3c&HFFFFFF&\\3a&H40&\\fad(200,0)}%s{\\p0}" % (a, b, rr(60, 470, 340, 830, 36)),
        "Dialogue: 1,%s,%s,box,,0,0,0,,{\\an7\\pos(0,0)\\p1\\1c&HFFFFFF&\\1a&HD8&\\bord3\\3c&HFFFFFF&\\3a&H40&\\fad(200,0)}%s{\\p0}" % (a, b, rr(380, 470, 660, 830, 36)),
        "Dialogue: 2,%s,%s,l,,0,0,0,,{\\an5\\pos(200,760)\\fad(200,0)}%s" % (a, b, la),
        "Dialogue: 2,%s,%s,l,,0,0,0,,{\\an5\\pos(520,760)\\fad(200,0)}%s" % (a, b, lb),
        "Dialogue: 2,%s,%s,s,,0,0,0,,{\\an5\\pos(360,920)\\fad(200,0)\\t(0,500,\\fscx106\\fscy106)\\t(500,1000,\\fscx100\\fscy100)\\t(1000,1500,\\fscx106\\fscy106)\\t(1500,2000,\\fscx100\\fscy100)}%s" % (a, b, os.environ.get("ENDCARD_HINT", "絵文字ひとつでコメントしてね")),
        "Dialogue: 2,%s,%s,s,,0,0,0,,{\\an5\\pos(360,1060)\\fs30\\c&HCCCCCC&\\fad(200,0)}%s" % (a, b, nxt),
    ]
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def main(inp, out, start, q, ea, la, eb, lb, nxt, hold=1.5):
    tmp = tempfile.mkdtemp()
    pa, pb, pd = (os.path.join(tmp, n) for n in ("a.png", "b.png", "d.png"))
    emoji_png(ea, pa); emoji_png(eb, pb); emoji_png("👇", pd, 70)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", inp]).decode())
    end = dur + hold
    ass = os.path.join(tmp, "c.ass"); ass_text(ass, q, la, lb, nxt, start, end + 1)
    en = "between(t,%.2f,%.2f)" % (start, end + 1)
    fc = ("[0:v]tpad=stop_mode=clone:stop_duration=%.2f,ass=%s[v];"
          "[v][1]overlay=x=125:y=520:enable='%s'[v1];[v1][2]overlay=x=445:y=520:enable='%s'[v2];"
          "[v2][3]overlay=x=325:y=960:enable='%s'[vo];[0:a]apad=pad_dur=%.2f[ao]") % (hold, ass, en, en, en, hold)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", inp, "-loop", "1", "-i", pa, "-loop", "1", "-i", pb, "-loop", "1", "-i", pd,
                    "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]", "-t", "%.3f" % end,
                    "-c:v", "libx264", "-crf", "20", "-maxrate", "6M", "-bufsize", "12M", "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print("wrote", out, "%.1f" % end)

if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], float(a[2]), a[3], a[4], a[5], a[6], a[7], a[8], float(a[9]) if len(a) > 9 else 1.5)

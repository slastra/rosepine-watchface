"""Generate res/raw/watchface.xml (run by build.sh; edit this, not the XML).

Layout: a terminal-instrument dial. Four bezel gauges, one per quadrant, each
anchored at 12 or 6 o'clock and growing toward 3/9, colored like the metric
beside it. Gaps at the cardinals hold ticks (none at 6, where the system's
status pill sits). Inside: a 60-dot minute track with an iris seconds dot,
stacked hours over minutes, metrics in the four corners, date below.
"""
import math
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

C = 225  # canvas center (450x450)

# Rosé Pine
BASE, SURFACE, OVERLAY = "#ff191724", "#ff1f1d2e", "#ff26233a"
MUTED, SUBTLE, TEXT = "#ff6e6a86", "#ff908caa", "#ffe0def4"
HL_MED, HL_HIGH = "#ff403d52", "#ff524f67"
LOVE, GOLD, ROSE, FOAM, IRIS = "#ffeb6f92", "#fff6c177", "#ffebbcba", "#ff9ccfd8", "#ffc4a7e7"

ICON_PULSE, ICON_BOLT, ICON_FOOT = "\U000F05F6", "\U000F140B", "\U000F0F52"

# WEATHER.CONDITION -> Nerd Font glyph. First match wins, so day-only cases precede their night fallback.
CLEAR, PARTLY = "([WEATHER.CONDITION] == 1 || [WEATHER.CONDITION] == 8)", "[WEATHER.CONDITION] == 14"
WEATHER_ICONS = [
    (f"{CLEAR} && [WEATHER.IS_DAY]", "\U000F0599"),   # sunny
    (CLEAR, "\U000F0594"),                            # clear night
    (f"{PARTLY} && [WEATHER.IS_DAY]", "\U000F0595"),  # partly cloudy
    (PARTLY, "\U000F0F31"),                           # partly cloudy night
    ("[WEATHER.CONDITION] == 2", "\U000F0590"),       # cloudy
    ("[WEATHER.CONDITION] == 3", "\U000F0591"),       # fog
    ("[WEATHER.CONDITION] == 13", "\U000F0F30"),      # mist
    ("[WEATHER.CONDITION] == 4", "\U000F0596"),       # heavy rain
    ("[WEATHER.CONDITION] == 6 || [WEATHER.CONDITION] == 12", "\U000F0597"),  # rain, light rain
    ("[WEATHER.CONDITION] == 5", "\U000F0F36"),       # heavy snow
    ("[WEATHER.CONDITION] == 7 || [WEATHER.CONDITION] == 11", "\U000F0598"),  # snow, light snow
    ("[WEATHER.CONDITION] == 10", "\U000F067F"),      # sleet
    ("[WEATHER.CONDITION] == 9", "\U000F067E"),       # thunderstorm
    ("[WEATHER.CONDITION] == 15", "\U000F059D"),      # windy
]
ICON_WEATHER_UNKNOWN = "\U000F050F"  # thermometer

# Gauges: 58 degree arcs; 40 degree gaps at 12 and 6 (6 clears the status pill), 24 at 3 and 9
# (0 = 12 o'clock, clockwise)
RING_D, RING_W, SPAN = 426, 7, 58
DOT_R = 194  # minute track radius

out = []
w = out.append


def interactive_only(indent):
    return f'{" " * indent}<Variant mode="AMBIENT" target="alpha" value="0" />'


def gauge(color, fraction, anchor, grow_cw):
    """Track plus progress arc. anchor is the fixed end; the arc grows away from it."""
    start, end = (anchor, anchor + SPAN) if grow_cw else (anchor - SPAN, anchor)
    if grow_cw:
        prog = f'startAngle="{anchor}" endAngle="{anchor}"', f'<Transform target="endAngle" value="{anchor} + {SPAN} * {fraction}" />'
    else:
        prog = f'startAngle="{anchor}" endAngle="{anchor}"', f'<Transform target="startAngle" value="{anchor} - {SPAN} * {fraction}" />'
    o = C - RING_D // 2
    return f"""        <PartDraw x="0" y="0" width="450" height="450">
{interactive_only(12)}
            <Arc centerX="{C}" centerY="{C}" width="{RING_D}" height="{RING_D}" startAngle="{start}" endAngle="{end}">
                <Stroke color="{OVERLAY}" thickness="{RING_W}" cap="ROUND" />
            </Arc>
            <Arc centerX="{C}" centerY="{C}" width="{RING_D}" height="{RING_D}" {prog[0]}>
                {prog[1]}
                <Stroke color="{color}" thickness="{RING_W}" cap="ROUND" />
            </Arc>
        </PartDraw>
"""


def text(x, y, width, height, size, color, body, ambient_alpha=None, ellipsis=False):
    variant = f'\n            <Variant mode="AMBIENT" target="alpha" value="{ambient_alpha}" />' if ambient_alpha is not None else ""
    ell = ' ellipsis="true"' if ellipsis else ""
    return f"""        <PartText x="{x}" y="{y}" width="{width}" height="{height}">{variant}
            <Text align="CENTER"{ell}>
                <Font family="rp_date" size="{size}" color="{color}">{body}</Font>
            </Text>
        </PartText>
"""


# Nerd Font icons are drawn off-center in their cells and the runtime centers the cell,
# so shift each icon by the gap between its advance center and its outline center.
_font = TTFont("res/font/rp_date.ttf")
_glyphs, _cmap, _upm = _font.getGlyphSet(), _font.getBestCmap(), _font["head"].unitsPerEm


def optical_dx(glyph, size):
    g = _glyphs[_cmap[ord(glyph)]]
    pen = BoundsPen(_glyphs)
    g.draw(pen)
    xmin, _, xmax, _ = pen.bounds
    return round((g.width / 2 - (xmin + xmax) / 2) * size / _upm)


def icon(x, y, color, glyph, size=None):
    size = size or ICON_SIZE
    return text(x + optical_dx(glyph, size), y, COL_W, 30, size, color, glyph, ambient_alpha=0)


def tmpl(fmt, expr):
    return f'<Template>{fmt}<Parameter expression="{expr}" /></Template>'


def indent(block, n):
    return "".join(" " * n + line if line.strip() else line for line in block.splitlines(True))


# Metric columns sit just inside the minute track, beside the digits
LX, RX, COL_W = 40, 290, 120
# TIME_Y places the digits (measured 79-325 at TIME_Y 0) a few px above the dial center, where
# the eye reads center. Metric groups are centered on their digit row (measured on device).
TIME_Y = 15
UP_ICON_Y, UP_VAL_Y = 100 + TIME_Y, 128 + TIME_Y      # icon over value, beside hours
LO_VAL_Y, LO_SUB_Y = 232 + TIME_Y, 276 + TIME_Y      # value over icon, beside minutes
VAL_H, VAL_SIZE, ICON_SIZE = 46, 38, 26

w(f"""<?xml version="1.0" encoding="utf-8"?>
<!-- Generated by extras/gen_face.py; edit that, not this. -->
<WatchFace width="450" height="450">
    <Metadata key="CLOCK_TYPE" value="DIGITAL" />
    <Metadata key="PREVIEW_TIME" value="10:08:32" />

    <Scene backgroundColor="#ff000000">
        <!-- Surface-to-base glow; dropped in ambient so AOD stays black -->
        <PartDraw x="0" y="0" width="450" height="450">
{interactive_only(12)}
            <Rectangle x="0" y="0" width="450" height="450">
                <Fill color="{BASE}">
                    <RadialGradient centerX="{C}" centerY="{C - 20}" radius="250" colors="{SURFACE} {BASE}" positions="0 1" />
                </Fill>
            </Rectangle>
        </PartDraw>

        <!-- Bezel gauges: battery UL, steps UR (10k goal), rain chance LR, heart rate LL (40-180) -->
""")
w(gauge(ROSE, "clamp([BATTERY_PERCENT] / 100.0, 0, 1)", 340, grow_cw=False))
w(gauge(FOAM, "clamp([STEP_COUNT] / 10000.0, 0, 1)", 20, grow_cw=True))
w(gauge(LOVE, "clamp(([HEART_RATE] - 40) / 140.0, 0, 1)", 200, grow_cw=True))
w(gauge(GOLD, "clamp([WEATHER.CHANCE_OF_PRECIPITATION] / 100.0, 0, 1)", 160, grow_cw=False))

# Cardinal ticks in the gauge gaps (6 o'clock left clear for the status pill)
ticks = []
for deg in (0, 90, 270):
    a = math.radians(deg)
    r0, r1 = RING_D / 2 - 8, RING_D / 2 + 8
    x0, y0 = C + r0 * math.sin(a), C - r0 * math.cos(a)
    x1, y1 = C + r1 * math.sin(a), C - r1 * math.cos(a)
    ticks.append(f'            <Line startX="{x0:.1f}" startY="{y0:.1f}" endX="{x1:.1f}" endY="{y1:.1f}">\n'
                 f'                <Stroke color="{MUTED}" thickness="3" cap="ROUND" />\n            </Line>')

# Minute track: 60 dots, hour positions a touch larger and brighter
dots = []
for i in range(60):
    a = math.radians(i * 6)
    r = 2.6 if i % 5 == 0 else 1.6
    color = HL_HIGH if i % 5 == 0 else HL_MED
    x, y = C + DOT_R * math.sin(a), C - DOT_R * math.cos(a)
    dots.append(f'            <Ellipse x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}"><Fill color="{color}" /></Ellipse>')

w(f"""
        <PartDraw x="0" y="0" width="450" height="450">
{interactive_only(12)}
{chr(10).join(ticks)}
{chr(10).join(dots)}
        </PartDraw>

        <!-- Seconds: an iris dot stepping around the minute track -->
        <PartDraw x="0" y="0" width="450" height="450" pivotX="0.5" pivotY="0.5" angle="0">
{interactive_only(12)}
            <Transform target="angle" value="[SECOND] * 6" />
            <Ellipse x="{C - 4.5}" y="{C - DOT_R - 4.5}" width="9" height="9"><Fill color="{IRIS}" /></Ellipse>
        </PartDraw>

        <!-- Hours over minutes -->
        <DigitalClock x="0" y="{58 + TIME_Y}" width="450" height="160">
            <Variant mode="AMBIENT" target="alpha" value="215" />
            <TimeText x="0" y="0" width="450" height="160" format="hh" hourFormat="SYNC_TO_DEVICE" align="CENTER">
                <Font family="rp_hours" size="156" color="{TEXT}" />
            </TimeText>
        </DigitalClock>
        <DigitalClock x="0" y="{196 + TIME_Y}" width="450" height="160">
            <Variant mode="AMBIENT" target="alpha" value="215" />
            <TimeText x="0" y="0" width="450" height="160" format="mm" align="CENTER">
                <Font family="rp_minutes" size="156" color="{IRIS}" />
            </TimeText>
        </DigitalClock>

        <!-- Battery (upper left) -->
""")
w(icon(LX, UP_ICON_Y, ROSE, ICON_BOLT))
w(text(LX, UP_VAL_Y, COL_W, VAL_H, VAL_SIZE, ROSE, tmpl("%d", "[BATTERY_PERCENT]"), ambient_alpha=150))

w("\n        <!-- Steps (upper right) -->\n")
w(icon(RX, UP_ICON_Y, FOAM, ICON_FOOT))
w(text(RX, UP_VAL_Y, COL_W, VAL_H, 34, FOAM, tmpl("%d", "[STEP_COUNT]"), ambient_alpha=150))

w(f"""
        <!-- Heart rate (lower left): dashes until there is a reading -->
        <Condition>
            <Expressions>
                <Expression name="hasPulse"><![CDATA[[HEART_RATE] > 0]]></Expression>
            </Expressions>
            <Compare expression="hasPulse">
{indent(text(LX, LO_VAL_Y, COL_W, VAL_H, VAL_SIZE, LOVE, tmpl("%d", "[HEART_RATE]"), ambient_alpha=150), 8)}            </Compare>
            <Default>
{indent(text(LX, LO_VAL_Y, COL_W, VAL_H, VAL_SIZE, LOVE, "--", ambient_alpha=150), 8)}            </Default>
        </Condition>
""")
w(icon(LX, LO_SUB_Y, LOVE, ICON_PULSE))

w(f"""
        <!-- Weather (lower right): temperature, dashes when unavailable -->
        <Condition>
            <Expressions>
                <Expression name="hasWeather"><![CDATA[[WEATHER.IS_AVAILABLE]]]></Expression>
            </Expressions>
            <Compare expression="hasWeather">
{indent(text(RX, LO_VAL_Y, COL_W, VAL_H, VAL_SIZE, GOLD, tmpl("%d°", "[WEATHER.TEMPERATURE]"), ambient_alpha=150), 8)}            </Compare>
            <Default>
{indent(text(RX, LO_VAL_Y, COL_W, VAL_H, VAL_SIZE, GOLD, "--", ambient_alpha=150), 8)}            </Default>
        </Condition>

        <!-- Weather condition icon -->
        <Condition>
            <Expressions>
""")
for i, (expr, _) in enumerate(WEATHER_ICONS):
    w(f'                <Expression name="wx{i}"><![CDATA[{expr}]]></Expression>\n')
w("            </Expressions>\n")
for i, (_, glyph) in enumerate(WEATHER_ICONS):
    w(f'            <Compare expression="wx{i}">\n{indent(icon(RX, LO_SUB_Y, GOLD, glyph, 28), 8)}            </Compare>\n')
w(f"""            <Default>
{indent(icon(RX, LO_SUB_Y, GOLD, ICON_WEATHER_UNKNOWN, 28), 8)}            </Default>
        </Condition>

        <!-- Date at the top, between the minute track and the hours -->
""")
w(text(0, 46, 450, 32, 24, SUBTLE,
       '<Template>%s %s<Parameter expression="[MONTH_S]" /><Parameter expression="[DAY]" /></Template>',
       ambient_alpha=160))
w("\n        <!-- Full weekday at the bottom -->\n")
w(text(0, 354, 450, 40, 30, SUBTLE, tmpl("%s", "[DAY_OF_WEEK_F]"), ambient_alpha=160))
w("""    </Scene>
</WatchFace>
""")

with open(sys.argv[1] if len(sys.argv) > 1 else "res/raw/watchface.xml", "w") as f:
    f.write("".join(out))

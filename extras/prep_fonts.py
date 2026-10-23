import sys, os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

L = os.path.expanduser("~/.local/share/fonts/")
T = "/usr/share/fonts/TTF/"
R = T + "Recursive/"
# Nerd Font glyphs used by the face: heart-pulse, lightning bolt, footprint, then weather
ICONS = [0xF05F6, 0xF140B, 0xF0F52,
         # weather: sunny, night, partly cloudy (day/night), cloudy, fog, hazy, pouring,
         # rainy, snowy heavy, snowy, sleet, lightning-rainy, windy, thermometer
         0xF0599, 0xF0594, 0xF0595, 0xF0F31, 0xF0590, 0xF0591, 0xF0F30, 0xF0596,
         0xF0597, 0xF0F36, 0xF0598, 0xF067F, 0xF067E, 0xF059D, 0xF050F]
# name: (hours, minutes, date); each (file, wght for variable fonts or None)
SETS = {
    "shure":   ((T+"ShureTechMonoNerdFont-Regular.ttf", None),) * 3,
    "iosevka": ((T+"IosevkaNerdFont-Bold.ttf", None), (T+"IosevkaNerdFont-Light.ttf", None), (T+"IosevkaNerdFont-Regular.ttf", None)),
    "bebas":   ((L+"BebasNeue-Regular.ttf", None),) * 3,
    "poppins": ((L+"Poppins-Bold.ttf", None), (L+"Poppins-ExtraLight.ttf", None), (L+"Poppins-Medium.ttf", None)),
    "jost":    ((L+"Jost-VariableFont_wght.ttf", 600), (L+"Jost-VariableFont_wght.ttf", 300), (L+"Jost-VariableFont_wght.ttf", 400)),
    "oswald":  ((L+"Oswald-VariableFont_wght.ttf", 600), (L+"Oswald-VariableFont_wght.ttf", 300), (L+"Oswald-VariableFont_wght.ttf", 400)),
    "urbanist":((L+"Urbanist-VariableFont_wght.ttf", 700), (L+"Urbanist-VariableFont_wght.ttf", 300), (L+"Urbanist-VariableFont_wght.ttf", 500)),
    "recmono": ((R+"RecMonoCasual-Bold-1.085.ttf", None), (R+"RecMonoCasual-Regular-1.085.ttf", None), (R+"RecMonoCasual-Regular-1.085.ttf", None)),
    "poiret":  ((L+"PoiretOne-Regular.ttf", None),) * 3,
}

out_root = sys.argv[1]
opts = subset.Options(); opts.layout_features = ["*"]; opts.name_IDs = ["*"]; opts.notdef_outline = True
for name, slots in SETS.items():
    d = os.path.join(out_root, name); os.makedirs(d, exist_ok=True)
    for slot, (path, wght) in zip(("rp_hours", "rp_minutes", "rp_date"), slots):
        f = TTFont(path)
        if "fvar" in f:
            f = instancer.instantiateVariableFont(f, {"wght": wght})
        s = subset.Subsetter(opts); s.populate(unicodes=list(range(0x20, 0x7f)) + [0xb0] + ICONS); s.subset(f)
        f.save(os.path.join(d, slot + ".ttf"))
    print(name, sum(os.path.getsize(os.path.join(d, x)) for x in os.listdir(d)) // 1024, "KB")

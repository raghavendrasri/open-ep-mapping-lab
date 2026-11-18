"""Original schematic hero drawing for the Learning Hub: a chamber outline filled with activation-coloured points
spreading from one early site, and a multi-spline mapping catheter. No quantitative claim."""
import math
W, H = 600, 520
stops = [(215,48,39),(244,109,67),(253,174,97),(254,224,139),(217,239,139),(102,189,99),(50,136,189),(94,79,162)]
def col(t):
    t = max(0.0, min(0.999, t)); f = t*(len(stops)-1); i = int(f); u = f-i
    a, b = stops[i], stops[i+1]
    return "#%02x%02x%02x" % tuple(round(a[k]+(b[k]-a[k])*u) for k in range(3))
cx, cy = 285, 285
def r_edge(ang):   # a chamber-like blob
    return 175*(1+0.10*math.sin(3*ang+0.6)+0.06*math.sin(5*ang)+0.04*math.cos(2*ang))
def inside(x, y):
    dx, dy = x-cx, (y-cy)*1.12
    return math.hypot(dx, dy) < r_edge(math.atan2(dy, dx))
# outline path
pts = []
for k in range(73):
    ang = 2*math.pi*k/72
    r = r_edge(ang)
    pts.append((cx+r*math.cos(ang), cy+r*math.sin(ang)/1.12))
path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
focal = (235, 215)
dots = []
dmax = 255
for gx in range(100, 480, 15):
    for gy in range(95, 480, 15):
        x = gx + 3*math.sin(gy*1.7); y = gy + 3*math.cos(gx*1.3)
        if inside(x, y):
            d = math.hypot(x-focal[0], y-focal[1])
            dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.6" fill="{col(d/dmax)}"/>')
# catheter: shaft from the upper right, splines fanning toward the early site
shaft = '<path d="M610,60 C560,95 520,120 470,150" fill="none" stroke="#9fb3b8" stroke-width="7" stroke-linecap="round"/>'
splines, elec = [], []
hub = (470, 150)
for k, deg in enumerate([115, 150, 185, 220, 255]):
    a = math.radians(deg)
    ex = 268 + 62*math.cos(a); ey = 228 + 62*math.sin(a)
    mx = (hub[0]+ex)/2 + 18*math.cos(a+1.2); my = (hub[1]+ey)/2 - 30 + 14*math.sin(a+1.2)
    splines.append(f'<path d="M{hub[0]},{hub[1]} Q{mx:.1f},{my:.1f} {ex:.1f},{ey:.1f}" fill="none" stroke="#cfe3e6" stroke-width="2"/>')
    for s in (0.35, 0.55, 0.75, 0.95):
        bx = (1-s)**2*hub[0] + 2*(1-s)*s*mx + s*s*ex
        by = (1-s)**2*hub[1] + 2*(1-s)*s*my + s*s*ey
        elec.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="3.2" fill="#5eead4" stroke="#0b3a40" stroke-width="1"/>')
svg = f'''<svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Schematic drawing: a heart chamber outline filled with coloured points, red at one early site and shading through yellow and green to purple far from it, with a multi-spline mapping catheter touching the early region" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="hubbg" cx="45%" cy="45%" r="75%"><stop offset="0" stop-color="#123840"/><stop offset="1" stop-color="#061317"/></radialGradient></defs>
<rect width="{W}" height="{H}" fill="url(#hubbg)"/>
<path d="{path}" fill="rgba(255,255,255,0.04)" stroke="rgba(207,227,230,0.45)" stroke-width="2"/>
<path d="M232,118 C228,80 236,55 250,40 M318,112 C326,76 340,58 356,48 M150,205 C120,190 98,186 76,190" fill="none" stroke="rgba(207,227,230,0.35)" stroke-width="10" stroke-linecap="round"/>
{"".join(dots)}
<circle cx="{focal[0]}" cy="{focal[1]}" r="8" fill="#ffffff"/><circle cx="{focal[0]}" cy="{focal[1]}" r="5" fill="#d73027"/>
{shaft}{"".join(splines)}{"".join(elec)}
</svg>'''
open(__import__("pathlib").Path(__file__).with_name("hero.svg"), "w").write(svg)
print(len(svg), "bytes,", len(dots), "dots")

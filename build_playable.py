#!/usr/bin/env python3
"""Build a single-file MRAID v2.0 compliant playable ad from index.html + assets."""

import base64, os, re, json

ASSETS_DIR = 'assets'

def b64_uri(filepath):
    ext = filepath.rsplit('.', 1)[-1].lower()
    mime_map = {
        'otf': 'font/otf', 'mp3': 'audio/mpeg', 'wav': 'audio/wav',
        'jpg': 'image/jpeg', 'png': 'image/png'
    }
    mime = mime_map.get(ext, 'application/octet-stream')
    with open(filepath, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    return f'data:{mime};base64,{data}'

# Base64 encode all needed assets
b64 = {}
asset_files = [
    'BentonSans-Cond.otf', 'BentonSans-CondBold.otf', 'GoudyTrajan-Bold.otf',
    'map.png', 'fleet-icon.png', 'target-marker.png', 'splash.jpg',
    'march-line.png', 'title-fire.png', 'title-logo.png', 'pointer.png', 'music.mp3',
    'knight-run-blue.png', 'knight-run-red.png', 'knight-sheet-blue.png', 'knight-sheet-red.png'
]
houses = ['stark', 'lannister', 'targaryen', 'baratheon', 'greyjoy', 'tully', 'martell', 'tyrell', 'arryn']

for f in asset_files:
    path = os.path.join(ASSETS_DIR, f)
    if os.path.exists(path):
        b64[f] = b64_uri(path)

for house in houses:
    path = os.path.join(ASSETS_DIR, f'{house}.png')
    if os.path.exists(path):
        b64[f'{house}.png'] = b64_uri(path)

# Read original HTML
with open('index.html') as f:
    html = f.read()

# Extract script
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
game_code = script_match.group(1)

# ── Modifications to game code ──

# Replace resize for fullscreen both orientations
game_code = game_code.replace(
    "function resize() {\n  const maxW = Math.min(window.innerWidth, 430);\n  const maxH = Math.min(window.innerHeight, 932);\n  const aspect = 9 / 16;\n  let w = maxW;\n  let h = w / aspect;\n  if (h > maxH) { h = maxH; w = h * aspect; }\n  canvas.width = w;\n  canvas.height = h;\n}",
    "function resize() {\n  canvas.width = window.innerWidth;\n  canvas.height = window.innerHeight;\n}"
)

# Replace CTA with MRAID
game_code = game_code.replace(
    "function handleCTA() {\n  const STORE_URL = 'https://example.com/download';\n  if (typeof FbPlayableAd !== 'undefined' && FbPlayableAd.onCTAClick) {\n    FbPlayableAd.onCTAClick();\n  } else {\n    window.open(STORE_URL, '_blank');\n  }\n}",
    "function handleCTA() {\n  var STORE_URL = 'https://apps.apple.com/app/id0000000000';\n  if (typeof mraid !== 'undefined' && mraid.open) {\n    mraid.open(STORE_URL);\n  } else {\n    window.open(STORE_URL, '_blank');\n  }\n}"
)

# Replace asset URLs with base64
asset_replacements = {
    "mapImage.src = 'assets/map.png'": f"mapImage.src = '{b64['map.png']}'",
    "knightImage.src = 'assets/fleet-icon.png'": f"knightImage.src = '{b64['fleet-icon.png']}'",
    "selectionMarkerImage.src = 'assets/selection-marker.png'": "// selection-marker removed",
    "targetMarkerImage.src = 'assets/target-marker.png'": f"targetMarkerImage.src = '{b64['target-marker.png']}'",
    "splashImage.src = 'assets/splash.jpg'": f"splashImage.src = '{b64['splash.jpg']}'",
    "marchLineImage.src = 'assets/march-line.png'": f"marchLineImage.src = '{b64['march-line.png']}'",
    "titleFireImage.src = 'assets/title-fire.png'": f"titleFireImage.src = '{b64['title-fire.png']}'",
    "titleLogoImage.src = 'assets/title-logo.png'": f"titleLogoImage.src = '{b64['title-logo.png']}'",
    "pointerImage.src = 'assets/pointer.png'": f"pointerImage.src = '{b64['pointer.png']}'",
    "knightRunBlue.src = 'assets/knight-run-blue.png'": f"knightRunBlue.src = '{b64['knight-run-blue.png']}'",
    "knightRunRed.src = 'assets/knight-run-red.png'": f"knightRunRed.src = '{b64['knight-run-red.png']}'",
    "knightSheetBlue.src = 'assets/knight-sheet-blue.png'": f"knightSheetBlue.src = '{b64['knight-sheet-blue.png']}'",
    "knightSheetRed.src = 'assets/knight-sheet-red.png'": f"knightSheetRed.src = '{b64['knight-sheet-red.png']}'",
}
for old, new in asset_replacements.items():
    game_code = game_code.replace(old, new)

# Replace audio with base64
game_code = game_code.replace(
    "const bgMusic = new Audio('assets/music.mp3')",
    f"const bgMusic = new Audio('{b64['music.mp3']}')"
)

# Fix sfx_victory (file doesn't exist)
game_code = game_code.replace(
    "const sfxVictory = new Audio('assets/sfx_victory.wav');\nsfxVictory.volume = 1.0;",
    "const sfxVictory = { currentTime: 0, play: function() { return Promise.resolve(); } };"
)

# Remove selection marker tracking line
game_code = game_code.replace("trackAsset(selectionMarkerImage);\n", "")
game_code = game_code.replace("trackAsset(knightRunBlue);\n", "")
game_code = game_code.replace("trackAsset(knightRunRed);\n", "")
game_code = game_code.replace("trackAsset(knightSheetBlue);\n", "")
game_code = game_code.replace("trackAsset(knightSheetRed);\n", "")

# Castle base64 map
castle_b64_lines = ["const CASTLE_B64 = {"]
for house in houses:
    castle_b64_lines.append(f"  '{house}': '{b64[house + '.png']}',")
castle_b64_lines.append("};")
castle_b64_map = "\n".join(castle_b64_lines) + "\n"

game_code = game_code.replace(
    "const CASTLE_ASSETS = ",
    castle_b64_map + "const CASTLE_ASSETS = "
)

# Replace castle image src loading
game_code = game_code.replace(
    "img.src = `assets/${house}.png`",
    "img.src = CASTLE_B64[house]"
)

# Remove debug UI block
debug_block = """if (DEBUG) document.getElementById('debug-btn').style.display = 'block';
document.getElementById('debug-btn').addEventListener('click', () => {
  document.getElementById('debug-panel').classList.toggle('open');
});
document.getElementById('dbg-edit').addEventListener('change', (e) => {
  debugEditMode = e.target.checked;
  if (!debugEditMode) dragStartCastle = null;
});
document.getElementById('dbg-ai').addEventListener('change', (e) => { debugAIEnabled = e.target.checked; });
document.getElementById('dbg-speed').addEventListener('input', (e) => { debugSpeed = parseFloat(e.target.value); });
document.getElementById('dbg-overlay').addEventListener('change', (e) => { debugOverlay = e.target.checked; });
document.getElementById('dbg-reset').addEventListener('click', () => {
  initCastles();
  document.getElementById('debug-panel').classList.remove('open');
});
document.getElementById('dbg-clear-pos').addEventListener('click', () => {
  localStorage.removeItem(POSITIONS_KEY);
  initCastles();
  document.getElementById('debug-panel').classList.remove('open');
});

document.getElementById('dbg-export').addEventListener('click', () => {
  const out = document.getElementById('dbg-export-output');
  const positions = {};
  castles.forEach(cs => { positions[cs.id] = { px: parseFloat(cs.px.toFixed(4)), py: parseFloat(cs.py.toFixed(4)) }; });
  out.textContent = JSON.stringify(positions, null, 2);
  out.style.display = 'block';
});"""
game_code = game_code.replace(debug_block, "")

# Build font base64 strings
font_benton = b64['BentonSans-Cond.otf']
font_benton_bold = b64['BentonSans-CondBold.otf']
font_goudy = b64['GoudyTrajan-Bold.otf']

# ── Assemble final HTML ──
final = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="ad.size" content="width=320,height=480">
<title>Conquest of Westeros</title>
<script src="mraid.js"><\/script>
<style>
  @font-face {{
    font-family: 'BentonSans';
    src: url('{font_benton}') format('opentype');
    font-weight: normal;
  }}
  @font-face {{
    font-family: 'BentonSans';
    src: url('{font_benton_bold}') format('opentype');
    font-weight: bold;
  }}
  @font-face {{
    font-family: 'GoudyTrajan';
    src: url('{font_goudy}') format('opentype');
    font-weight: bold;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    background: #000;
    width: 100%;
    height: 100%;
    overflow: hidden;
    font-family: 'BentonSans', sans-serif;
  }}
  body {{
    display: flex;
    justify-content: center;
    align-items: center;
  }}
  canvas {{
    display: block;
    touch-action: none;
  }}
</style>
</head>
<body>
<canvas id="gameCanvas"></canvas>
<script>
(function() {{

var mraidReady = false;
var gameInitialized = false;
var adAudioAllowed = true;

function onMraidReady() {{
  mraidReady = true;
  if (mraid.isViewable()) {{
    startGame();
  }} else {{
    mraid.addEventListener('viewableChange', onViewableChange);
  }}
}}

function onViewableChange(viewable) {{
  if (viewable && !gameInitialized) {{
    startGame();
  }}
  if (!viewable) {{
    adAudioAllowed = false;
    try {{ bgMusic.pause(); }} catch(e) {{}}
  }}
}}

function onStateChange(state) {{
  if (state === 'hidden') {{
    adAudioAllowed = false;
    try {{ bgMusic.pause(); }} catch(e) {{}}
  }}
}}

if (typeof mraid !== 'undefined') {{
  if (mraid.getState() === 'loading') {{
    mraid.addEventListener('ready', onMraidReady);
  }} else {{
    onMraidReady();
  }}
  try {{ mraid.addEventListener('stateChange', onStateChange); }} catch(e) {{}}
}} else {{
  startGame();
}}

function startGame() {{
  if (gameInitialized) return;
  gameInitialized = true;

{game_code}

}} // end startGame

}})();
<\/script>
</body>
</html>'''

# Fix escaped script tags
final = final.replace('<\\/script>', '</script>')
final = final.replace('<\/script>', '</script>')

with open('playable_ad.html', 'w') as f:
    f.write(final)

size = os.path.getsize('playable_ad.html')
print(f'playable_ad.html: {size // 1024}KB ({size / (1024*1024):.1f}MB)')
if size < 5 * 1024 * 1024:
    print('✓ Under 5MB limit')
else:
    print('✗ OVER 5MB limit!')

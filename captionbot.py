"""
CaptionBot - voice note (or typed text) -> WhatsApp status caption.
Runs 100% on your laptop with Ollama + Gemma. No pip installs needed.

1. Make sure Ollama is running and you have pulled the model:  ollama pull gemma3:1b
2. Run:  python captionbot.py
3. Open http://localhost:8000 in CHROME (voice needs Chrome or Edge)
"""
import json, os, re, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

MODEL = os.environ.get("MODEL", "gemma3:1b")
OLLAMA = "http://localhost:11434/api/generate"

# Swap these for your seller's real listings later. Her own style = better captions.
EXAMPLES = """Details: 3 senator wear, sizes M L XL, 25k, Abuja delivery
Caption: Fresh senator wear just landed 🔥 Sizes M, L, XL. 25k each. Abuja delivery available. DM to order.

Details: 2 ankara skirt, size 8 and 10, Port Harcourt delivery
Caption: Two ankara skirts, sizes 8 and 10 ✨ Port Harcourt delivery available. DM to order."""

def build_prompt(details, strict=False):
    extra = "You MUST include the price exactly as given. " if strict else ""
    return f"""You write WhatsApp status captions for a Nigerian clothing seller.
The details may be in Nigerian Pidgin. Understand it, but write the caption in simple clear English.
Pidgin help: "I get" = I have. "na" = is. "dey" = is/are. "fit deliver" = can deliver. "fine" = beautiful. "abeg" = please. "for" = in/at.
Rules: Write ONE caption only. No options, no notes, no questions.
Use ONLY the details given. Never invent discounts, gifts, deadlines or style words.
If no price is given, do not mention any price or amount.
{extra}Keep the item names, sizes, price and delivery exactly as given.
No placeholders. End with "DM to order". Under 40 words, max 3 emojis.

{EXAMPLES}

Details: {details}
Caption:"""

def ask_ollama(prompt):
    body = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.3, "num_predict": 120},
    }).encode()
    req = urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        text = json.loads(r.read())["response"].strip()
    text = text.split("\n\n")[0].strip().strip('"').strip()
    return text

def facts(details):
    """Prices/numbers from the details that the caption must keep, e.g. 18k, 40000."""
    return re.findall(r"\d[\d,.]*\s?k?", details.lower())

def normalize(details):
    """Fix common mishears: '12 key' / '12 kay' / '12 thousand' -> '12k'."""
    d = re.sub(r"(\d)\s*(key|kay|ki|k\.|thousand|grand)\b", r"\1k", details, flags=re.I)
    d = re.sub(r"\blist (blouse|gown|top|dress)", r"lace \1", d, flags=re.I)
    return d

def generate(details):
    details = normalize(details)
    need = [f.replace(" ", "") for f in facts(details)]
    best = ""
    given_prices = {p.replace(" ", "") for p in re.findall(r"\d[\d,.]*\s?k\b", details.lower())}
    for attempt in range(3):
        cap = ask_ollama(build_prompt(details, strict=attempt > 0))
        flat = cap.lower().replace(" ", "")
        # reject captions that invent a price that was never given
        invented = [p for p in re.findall(r"\d[\d,.]*k\b", flat) if p not in given_prices]
        if all(n in flat for n in need) and not invented:
            return cap, attempt + 1
        best = best or cap
    return best, 3

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CaptionBot</title>
<style>
:root{--indigo:#1b2a6b;--saffron:#f2a900;--cream:#fbf7ef;--ink:#1a1a1a;--green:#128c4a}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);font-family:"Trebuchet MS",Verdana,sans-serif;line-height:1.5}
header{background:var(--indigo);color:#fff;padding:28px 20px 22px;border-bottom:6px solid var(--saffron)}
header h1{margin:0;font-size:1.7rem;letter-spacing:.2px}
header p{margin:6px 0 0;opacity:.85;max-width:44ch}
main{max-width:560px;margin:0 auto;padding:20px}
label{display:block;font-weight:bold;margin:0 0 6px}
textarea{width:100%;min-height:110px;padding:12px;border:2px solid var(--indigo);border-radius:6px;font:inherit;background:#fff}
button{font:inherit;font-weight:bold;border:0;border-radius:6px;padding:12px 16px;cursor:pointer}
button:focus-visible,textarea:focus-visible{outline:3px solid var(--saffron);outline-offset:2px}
.row{display:flex;gap:10px;margin:12px 0;flex-wrap:wrap}
#mic{background:var(--saffron);color:var(--ink);flex:1}
#mic.on{background:#c0392b;color:#fff}
#go{background:var(--indigo);color:#fff;flex:1}
button:disabled{opacity:.5;cursor:wait}
#out{display:none;margin-top:18px;background:#fff;border-left:6px solid var(--saffron);padding:16px;border-radius:6px}
#cap{white-space:pre-wrap;font-size:1.05rem;margin:0 0 12px}
#copy{background:#e8e8e8}
#wa{background:var(--green);color:#fff}
small{color:#555;display:block;margin-top:10px}
#err{color:#c0392b;margin-top:10px}
</style></head><body>
<header><h1>CaptionBot</h1><p>Say what you are selling. Get a WhatsApp status caption you can post.</p></header>
<main>
<label for="d">What are you selling?</label>
<textarea id="d" placeholder="2 ankara gown, size 12 and 14, 18k each, Lagos delivery"></textarea>
<div class="row">
<button id="mic" type="button">Tap to speak</button>
<button id="go" type="button">Write caption</button>
</div>
<div id="err" role="alert"></div>
<div id="out">
<p id="cap"></p>
<div class="row"><button id="copy" type="button">Copy</button><button id="wa" type="button">Send to WhatsApp</button></div>
<small id="meta"></small>
</div>
</main>
<script>
const d=document.getElementById('d'),mic=document.getElementById('mic'),go=document.getElementById('go'),
out=document.getElementById('out'),cap=document.getElementById('cap'),err=document.getElementById('err'),meta=document.getElementById('meta');
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
let rec=null,listening=false;
if(!SR){mic.disabled=true;mic.textContent="Voice needs Chrome or Edge"}
else{
  rec=new SR();rec.lang='en-NG';rec.interimResults=true;rec.continuous=true;
  let base='';
  rec.onresult=e=>{let t='';for(let i=0;i<e.results.length;i++)t+=e.results[i][0].transcript;d.value=(base+' '+t).trim()};
  rec.onend=()=>{listening=false;mic.classList.remove('on');mic.textContent='Tap to speak'};
  rec.onerror=e=>{err.textContent='Mic problem: '+e.error+'. Allow the microphone, or type instead.'};
  mic.onclick=()=>{
    err.textContent='';
    if(listening){rec.stop();return}
    base=d.value;listening=true;mic.classList.add('on');mic.textContent='Listening... tap to stop';rec.start();
  };
}
go.onclick=async()=>{
  const details=d.value.trim();err.textContent='';
  if(!details){err.textContent='Say or type what you are selling first.';return}
  if(listening&&rec)rec.stop();
  go.disabled=true;go.textContent='Writing...';out.style.display='none';
  try{
    const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({details})});
    const j=await r.json();
    if(!r.ok)throw new Error(j.error||'Failed');
    cap.textContent=j.caption;out.style.display='block';
    meta.textContent=j.tries>1?'Took '+j.tries+' tries to keep your price and sizes right. Always read it before posting.':'Read it before you post.';
  }catch(e){err.textContent='Could not write the caption. Is Ollama running? ('+e.message+')'}
  go.disabled=false;go.textContent='Write caption';
};
document.getElementById('copy').onclick=async e=>{
  try{await navigator.clipboard.writeText(cap.textContent);e.target.textContent='Copied'}catch{e.target.textContent='Press and hold the text to copy'}
  setTimeout(()=>e.target.textContent='Copy',1800);
};
document.getElementById('wa').onclick=()=>window.open('https://wa.me/?text='+encodeURIComponent(cap.textContent),'_blank');
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.end_headers()
        self.wfile.write(body if isinstance(body, bytes) else body.encode())

    def do_GET(self):
        self._send(200, PAGE, "text/html")

    def do_POST(self):
        if self.path != "/generate":
            return self._send(404, json.dumps({"error": "not found"}))
        try:
            n = int(self.headers.get("Content-Length", 0))
            details = json.loads(self.rfile.read(n))["details"][:500]
            caption, tries = generate(details)
            self._send(200, json.dumps({"caption": caption, "tries": tries}))
        except Exception as e:
            self._send(500, json.dumps({"error": str(e)}))

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"CaptionBot running with {MODEL}. Open http://localhost:8000 in Chrome.")
    HTTPServer(("127.0.0.1", 8000), H).serve_forever()

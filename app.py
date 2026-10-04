"""Named Q&A link. Run: pip install flask && ADMIN_KEY=yourSecret OWNER=moon python app.py
Public page:  /          (share this link)
Your inbox:   /inbox?key=yourSecret   (shows who asked what)
Deploy free on Render / Railway / PythonAnywhere; set ADMIN_KEY and OWNER env vars."""
import os, sqlite3, time
from flask import Flask, request, render_template_string, redirect, abort, jsonify

app = Flask(__name__)
DB = os.environ.get("DB", "questions.db")
OWNER = os.environ.get("OWNER", "moon")
KEY = os.environ.get("ADMIN_KEY", "change-me")

def db():
    c = sqlite3.connect(DB)
    c.execute("create table if not exists q(id integer primary key, name text, question text, ts real)")
    return c

CSS = """
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:'Nunito',system-ui,sans-serif;
background:linear-gradient(135deg,#d6317f 0%,#e8604c 55%,#f29a3c 100%);color:#fff;display:flex;justify-content:center}
main{width:100%;max-width:440px;padding:56px 18px 32px}
.card{background:#fff;color:#111;border-radius:36px;overflow:hidden}
.head{display:flex;gap:16px;align-items:center;padding:22px 24px}
.av{width:60px;height:60px;border-radius:50%;background:#7b5cd6;color:#fff;display:grid;place-items:center;font-size:28px;font-weight:800;flex:none}
.head b{font-size:22px;display:block}.head span{font-size:20px;font-weight:700}
.box{position:relative;background:linear-gradient(135deg,rgba(214,49,127,.45),rgba(242,154,60,.45));padding:6px 24px 24px}
input,textarea{width:100%;background:transparent;border:0;outline:0;color:#3b0a26;font:inherit;font-size:22px;font-weight:700}
input{border-bottom:2px solid rgba(59,10,38,.35);padding:14px 0;margin-top:8px}
textarea{height:130px;resize:none;padding-top:14px}
::placeholder{color:rgba(59,10,38,.5)}
.dice{position:absolute;right:16px;bottom:14px;width:52px;height:52px;border-radius:50%;border:0;background:rgba(255,255,255,.35);font-size:26px;cursor:pointer}
.note{text-align:center;font-weight:700;font-size:19px;margin:22px 0 16px}
.btn{display:block;width:100%;background:#000;color:#fff;border:0;border-radius:99px;padding:22px;font:inherit;font-size:26px;font-weight:800;text-align:center;text-decoration:none;cursor:pointer;box-shadow:0 10px 24px rgba(0,0,0,.18)}
.btn:focus-visible,input:focus-visible,textarea:focus-visible,.dice:focus-visible{outline:3px solid #fff;outline-offset:3px}
.msg{text-align:center;margin-top:18px;font-weight:700;min-height:24px}
.row{background:#fff;color:#111;border-radius:22px;padding:16px 20px;margin:12px 0}.row small{color:#a03a68;font-weight:800}
"""

PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Ask @{{o}}</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800&display=swap" rel=stylesheet>
<style>{{css|safe}}</style></head><body><main>
<div class=card><div class=head><div class=av>{{o[0]|upper}}</div><div><b>@{{o}}</b><span>ask me a question!</span></div></div>
<div class=box><input id=n maxlength=40 placeholder="your name" autocomplete=name required>
<textarea id=q maxlength=500 placeholder="are u single?" required></textarea>
<button class=dice type=button id=d aria-label="Random question">🎲</button></div></div>
<p class=note>🔓 named q&a — @{{o}} will not be able to see your name</p>
<button class=btn id=s>Send!</button><div class=msg id=m role=status></div>
<p style="text-align:center;margin-top:40px;font-weight:700;opacity:.8"><a href="https://render.com" style="color:#fff;display:none"></a></p>
</main><script>
const ideas=["are u single?","what's your biggest dream?","what's the last song you played?","coffee or tea?","what are you into lately?","best advice you've got?"];
const q=document.getElementById('q'),n=document.getElementById('n'),m=document.getElementById('m');
document.getElementById('d').onclick=()=>{q.value=ideas[Math.floor(Math.random()*ideas.length)]};
document.getElementById('s').onclick=async()=>{
 if(!n.value.trim()||!q.value.trim()){m.textContent='Add your name and a question.';return}
 const r=await fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n.value,question:q.value})});
 if(r.ok){q.value='';m.textContent='Sent! @{{o}} cannot see it was you!.'}else m.textContent='Something went wrong. Try again.'};
</script></body></html>"""

INBOX = """<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><title>Inbox</title>
<style>{{css|safe}}</style><main><h2>Questions for @{{o}} ({{rows|length}})</h2>
{% for r in rows %}<div class=row><small>{{r[0]}} · {{r[2]}}</small><p>{{r[1]}}</p></div>{% else %}<p>No questions yet.</p>{% endfor %}</main>"""

@app.get("/")
def home():
    return render_template_string(PAGE, o=OWNER, css=CSS)

@app.post("/send")
def send():
    d = request.get_json(silent=True) or {}
    name, qu = str(d.get("name", "")).strip()[:40], str(d.get("question", "")).strip()[:500]
    if not name or not qu:
        abort(400)
    with db() as c:
        c.execute("insert into q(name,question,ts) values(?,?,?)", (name, qu, time.time()))
    return jsonify(ok=True)

@app.get("/inbox")
def inbox():
    if request.args.get("key") != KEY:
        abort(403)
    with db() as c:
        rows = [(n, q, time.strftime("%b %d, %H:%M", time.localtime(t)))
                for n, q, t in c.execute("select name,question,ts from q order by id desc")]
    return render_template_string(INBOX, o=OWNER, rows=rows, css=CSS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

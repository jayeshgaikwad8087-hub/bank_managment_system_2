from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, re, datetime, secrets, logging

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE_DIR,"app.db")
app=Flask(__name__,static_folder=None)
app.secret_key=os.environ.get("SECRET_KEY")
if not app.secret_key:
    app.secret_key=secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE","0")=="1",
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=7),
)
logging.basicConfig(level=logging.INFO)

def conn():
    c=sqlite3.connect(DB, timeout=15)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA journal_mode=WAL")
    return c

def init_db():
    c=conn()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id))""")
    c.commit(); c.close()
init_db()

def valid_email(x):
    return bool(re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",x or ""))

def user():
    uid=session.get("uid")
    if not uid: return None
    c=conn(); r=c.execute("SELECT id,name,email,created_at FROM users WHERE id=?",(uid,)).fetchone(); c.close()
    return dict(r) if r else None

@app.get("/")
def index(): return send_from_directory(BASE_DIR,"index.html")

@app.get("/favicon.ico")
def favicon(): return ("",204)

@app.get("/health")
def health(): return jsonify(ok=True,status="healthy",service="DSG 50 Page Workspace")

@app.post("/api/register")
def register():
    d=request.get_json(silent=True) or {}
    name=str(d.get("name","")).strip(); email=str(d.get("email","")).strip().lower(); pw=str(d.get("password",""))
    if not 2<=len(name)<=80: return jsonify(ok=False,message="Name must be 2-80 characters."),400
    if not valid_email(email) or len(email)>254: return jsonify(ok=False,message="Enter a valid email."),400
    if len(pw)<8 or not re.search(r"[A-Z]",pw) or not re.search(r"[a-z]",pw) or not re.search(r"\d",pw):
        return jsonify(ok=False,message="Password needs 8+ chars, uppercase, lowercase and number."),400
    c=conn()
    try:
        cur=c.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
                      (name,email,generate_password_hash(pw),datetime.datetime.now(datetime.timezone.utc).isoformat()))
        c.commit(); session.permanent=True; session["uid"]=cur.lastrowid
    except sqlite3.IntegrityError:
        c.close(); return jsonify(ok=False,message="Email already registered."),409
    c.close(); return jsonify(ok=True,user=user())

@app.post("/api/login")
def login():
    d=request.get_json(silent=True) or {}; email=str(d.get("email","")).strip().lower(); pw=str(d.get("password",""))
    c=conn(); r=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); c.close()
    if not r or not check_password_hash(r["password_hash"],pw): return jsonify(ok=False,message="Invalid email or password."),401
    session.permanent=True; session["uid"]=r["id"]; return jsonify(ok=True,user=user())

@app.post("/api/logout")
def logout(): session.clear(); return jsonify(ok=True)

@app.get("/api/me")
def me(): return jsonify(ok=True,authenticated=bool(user()),user=user())

@app.get("/api/notes")
def notes():
    u=user()
    if not u:return jsonify(ok=False,message="Login required."),401
    c=conn(); rows=c.execute("SELECT id,title,body,created_at FROM notes WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall(); c.close()
    return jsonify(ok=True,notes=[dict(x) for x in rows])

@app.post("/api/notes")
def add_note():
    u=user()
    if not u:return jsonify(ok=False,message="Login required."),401
    d=request.get_json(silent=True) or {}; title=str(d.get("title","")).strip(); body=str(d.get("body","")).strip()
    if not 2<=len(title)<=120 or not 1<=len(body)<=5000:return jsonify(ok=False,message="Invalid note length."),400
    c=conn(); cur=c.execute("INSERT INTO notes(user_id,title,body,created_at) VALUES(?,?,?,?)",(u["id"],title,body,datetime.datetime.now(datetime.timezone.utc).isoformat())); c.commit()
    r=c.execute("SELECT id,title,body,created_at FROM notes WHERE id=?",(cur.lastrowid,)).fetchone(); c.close(); return jsonify(ok=True,note=dict(r))

@app.delete("/api/notes/<int:nid>")
def delete_note(nid):
    u=user()
    if not u:return jsonify(ok=False,message="Login required."),401
    c=conn(); c.execute("DELETE FROM notes WHERE id=? AND user_id=?",(nid,u["id"])); c.commit(); c.close(); return jsonify(ok=True)

@app.errorhandler(404)
def fallback(e):
    if request.path.startswith("/api/"):
        return jsonify(ok=False,message="API route not found."),404
    return send_from_directory(BASE_DIR,"index.html")

@app.errorhandler(500)
def server_error(e):
    logging.exception("Unhandled server error")
    if request.path.startswith("/api/"):
        return jsonify(ok=False,message="Internal server error."),500
    return "Internal server error",500

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)

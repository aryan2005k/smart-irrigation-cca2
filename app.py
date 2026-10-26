import os, sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "database", "irrigation.db"))
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat()
from contextlib import contextmanager


@contextmanager
def connect():
    c = sqlite3.connect(DATABASE)
    c.row_factory = sqlite3.Row

    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()

def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS zones (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, crop TEXT NOT NULL,
          threshold INTEGER NOT NULL DEFAULT 35, mode TEXT NOT NULL DEFAULT 'auto',
          enabled INTEGER NOT NULL DEFAULT 1, moisture REAL NOT NULL DEFAULT 50,
          pump_on INTEGER NOT NULL DEFAULT 0, updated_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS sensor_readings (
          id INTEGER PRIMARY KEY AUTOINCREMENT, zone_id INTEGER NOT NULL, moisture REAL NOT NULL,
          temperature REAL, created_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS irrigation_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT, zone_id INTEGER NOT NULL, action TEXT NOT NULL,
          note TEXT, created_at TEXT NOT NULL)""")
        if c.execute("SELECT COUNT(*) FROM zones").fetchone()[0] == 0:
            for name,crop in [("Zone 1","Tomato"),("Zone 2","Potato"),("Zone 3","Onion")]:
                cur=c.execute("INSERT INTO zones(name,crop,threshold,updated_at) VALUES(?,?,35,?)",(name,crop,now()))
                c.execute("INSERT INTO sensor_readings(zone_id,moisture,temperature,created_at) VALUES(?,50,24,?)",(cur.lastrowid,now()))

def as_zone(row):
    d=dict(row); d["enabled"]=bool(d["enabled"]); d["pump_on"]=bool(d["pump_on"])
    d["irrigation_status"]="Irrigating" if d["pump_on"] else "Idle"
    return d

def auto_rule(c,zid):
    z=c.execute("SELECT * FROM zones WHERE id=?",(zid,)).fetchone()
    if not z: return
    pump=int(bool(z["enabled"]) and z["mode"]=="auto" and z["moisture"]<z["threshold"])
    if pump != z["pump_on"]:
        c.execute("UPDATE zones SET pump_on=?,updated_at=? WHERE id=?",(pump,now(),zid))
        c.execute("INSERT INTO irrigation_logs(zone_id,action,note,created_at) VALUES(?,?,?,?)",
                  (zid,"START" if pump else "STOP","Automatic moisture rule",now()))

@app.get("/")
def home(): return render_template("index.html")
@app.get("/zones")
def zones_page(): return render_template("zones.html")
@app.get("/health")
def health(): return jsonify(status="ok",service="smart-irrigation")

@app.get("/api/zones")
def get_zones():
    with connect() as c: rows=c.execute("SELECT * FROM zones ORDER BY id").fetchall()
    return jsonify([as_zone(r) for r in rows])

@app.get("/api/summary")
def summary():
    with connect() as c:
        rows=c.execute("SELECT * FROM zones").fetchall()
        starts=c.execute("SELECT COUNT(*) FROM irrigation_logs WHERE action='START'").fetchone()[0]
    return jsonify(zone_count=len(rows),irrigating=sum(bool(r["pump_on"]) for r in rows),
      average_moisture=round(sum(r["moisture"] for r in rows)/len(rows),1) if rows else 0,
      irrigation_starts=starts,data_mode="simulated")

@app.get("/api/history")
def history():
    with connect() as c:
        rows=c.execute("""SELECT sr.id,sr.zone_id,z.name AS zone_name,sr.moisture,sr.temperature,sr.created_at
          FROM sensor_readings sr JOIN zones z ON z.id=sr.zone_id ORDER BY sr.id DESC LIMIT 30""").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/logs")
def logs():
    with connect() as c:
        rows=c.execute("""SELECT l.id,z.name AS zone_name,l.action,l.note,l.created_at
          FROM irrigation_logs l JOIN zones z ON z.id=l.zone_id ORDER BY l.id DESC LIMIT 30""").fetchall()
    return jsonify([dict(r) for r in rows])

@app.patch("/api/zones/<int:zid>")
def update_zone(zid):
    p=request.get_json(silent=True) or {}; changes={}
    if "threshold" in p:
        try: t=int(p["threshold"])
        except (ValueError,TypeError): return jsonify(error="threshold must be an integer from 1 to 99"),400
        if not 1<=t<=99: return jsonify(error="threshold must be between 1 and 99"),400
        changes["threshold"]=t
    if "mode" in p:
        if p["mode"] not in ("auto","manual"): return jsonify(error="mode must be auto or manual"),400
        changes["mode"]=p["mode"]
    if "enabled" in p: changes["enabled"]=int(bool(p["enabled"]))
    if not changes: return jsonify(error="no valid fields supplied"),400
    with connect() as c:
        if not c.execute("SELECT id FROM zones WHERE id=?",(zid,)).fetchone(): return jsonify(error="zone not found"),404
        clause=", ".join(f"{k}=?" for k in changes)
        c.execute(f"UPDATE zones SET {clause},updated_at=? WHERE id=?",( *changes.values(),now(),zid))
        auto_rule(c,zid)
        row=c.execute("SELECT * FROM zones WHERE id=?",(zid,)).fetchone()
    return jsonify(as_zone(row))

@app.post("/api/zones/<int:zid>/control")
def control_zone(zid):
    action=(request.get_json(silent=True) or {}).get("action")
    if action not in ("start","stop"): return jsonify(error="action must be start or stop"),400
    with connect() as c:
        z=c.execute("SELECT * FROM zones WHERE id=?",(zid,)).fetchone()
        if not z: return jsonify(error="zone not found"),404
        if action=="start" and not z["enabled"]: return jsonify(error="zone is disabled"),409
        pump=int(action=="start")
        if pump != z["pump_on"]:
            c.execute("UPDATE zones SET pump_on=?,mode='manual',updated_at=? WHERE id=?",(pump,now(),zid))
            c.execute("INSERT INTO irrigation_logs(zone_id,action,note,created_at) VALUES(?,?,?,?)",
              (zid,action.upper(),"Manual dashboard control",now()))
        return jsonify(as_zone(c.execute("SELECT * FROM zones WHERE id=?",(zid,)).fetchone()))

@app.post("/api/simulate")
def simulate():
    p=request.get_json(silent=True) or {}
    with connect() as c:
        for z in c.execute("SELECT * FROM zones ORDER BY id").fetchall():
            try: m=float(p.get(str(z["id"]),max(10,min(90,z["moisture"]-4 if z["moisture"]>45 else z["moisture"]+7))))
            except (ValueError,TypeError): return jsonify(error=f"invalid moisture for zone {z['id']}"),400
            if not 0<=m<=100: return jsonify(error="moisture must be between 0 and 100"),400
            c.execute("UPDATE zones SET moisture=?,updated_at=? WHERE id=?",(m,now(),z["id"]))
            c.execute("INSERT INTO sensor_readings(zone_id,moisture,temperature,created_at) VALUES(?,?,?,?)",(z["id"],m,24,now()))
            auto_rule(c,z["id"])
    return jsonify(message="Simulated readings updated")

@app.post("/api/iot/readings")
def iot_reading():
    p=request.get_json(silent=True) or {}
    try: zid=int(p["zone_id"]); m=float(p["moisture"]); temp=float(p.get("temperature",24))
    except (KeyError,ValueError,TypeError): return jsonify(error="zone_id and numeric moisture are required"),400
    if not 0<=m<=100: return jsonify(error="moisture must be between 0 and 100"),400
    with connect() as c:
        if not c.execute("SELECT id FROM zones WHERE id=?",(zid,)).fetchone(): return jsonify(error="zone not found"),404
        c.execute("UPDATE zones SET moisture=?,updated_at=? WHERE id=?",(m,now(),zid))
        c.execute("INSERT INTO sensor_readings(zone_id,moisture,temperature,created_at) VALUES(?,?,?,?)",(zid,m,temp,now()))
        auto_rule(c,zid)
    return jsonify(message="reading accepted",zone_id=zid,moisture=m),201

init_db()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT","5000")))

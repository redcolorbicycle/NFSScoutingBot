import os
from datetime import timedelta
from urllib.parse import urlparse

import psycopg2
from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "changeme-set-in-heroku")
app.permanent_session_lifetime = timedelta(days=7)

WEB_PASSWORD = os.getenv("WEB_PASSWORD", "")

PR_COLORS = [
    (50,   "#FF6B6B"),
    (200,  "#FFA500"),
    (500,  "#FFD700"),
    (1000, "#ADD8E6"),
    (2000, "#D397F8"),
]


def pr_color(pr):
    if pr is None:
        return "#888"
    for threshold, color in PR_COLORS:
        if pr <= threshold:
            return color
    return "#888"


def get_db():
    url = os.getenv("DATABASE_URL")
    r = urlparse(url)
    return psycopg2.connect(
        database=r.path[1:], user=r.username,
        password=r.password, host=r.hostname, port=r.port,
    )


def fetch_dicts(cursor, query, params=()):
    cursor.execute(query, params)
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def fetch_one_dict(cursor, query, params=()):
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def guard():
    if WEB_PASSWORD and not session.get("authenticated"):
        return redirect(url_for("login"))
    return None


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == WEB_PASSWORD:
            session.permanent = True
            session["authenticated"] = True
            return redirect(url_for("clubs"))
        flash("Wrong password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Clubs ─────────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/clubs")
def clubs():
    g = guard()
    if g:
        return g
    conn = get_db()
    with conn.cursor() as cur:
        rows = fetch_dicts(cur, """
            SELECT c.club_name, COUNT(p.name) AS player_count
            FROM club c
            LEFT JOIN player p ON p.club_name = c.club_name
            GROUP BY c.club_name
            ORDER BY c.club_name
        """)
    conn.close()
    return render_template("clubs.html", clubs=rows)


# ── Club detail ───────────────────────────────────────────────────────────────

@app.route("/club/<club_name>")
def club(club_name):
    g = guard()
    if g:
        return g
    conn = get_db()
    with conn.cursor() as cur:
        players = fetch_dicts(cur, """
            SELECT name, nerf, pr, team_name, charbats, toolbats,
                   sp1_name, sp1_skills, sp2_name, sp2_skills,
                   sp3_name, sp3_skills, sp4_name, sp4_skills,
                   sp5_name, sp5_skills, last_updated, source
            FROM player
            WHERE club_name = %s
            ORDER BY pr
        """, (club_name,))
    conn.close()
    return render_template("club.html", club_name=club_name, players=players, pr_color=pr_color)


# ── Player detail ─────────────────────────────────────────────────────────────

@app.route("/player/<player_name>")
def player_detail(player_name):
    g = guard()
    if g:
        return g
    conn = get_db()
    with conn.cursor() as cur:
        p = fetch_one_dict(cur, """
            SELECT name, club_name, sp1_name, sp1_skills, sp2_name, sp2_skills,
                   sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name, sp5_skills,
                   nerf, pr, last_updated, nerf_updated, team_name, charbats, toolbats, source
            FROM player WHERE name = %s
        """, (player_name,))
    conn.close()
    if not p:
        flash(f"Player '{player_name}' not found.", "warning")
        return redirect(url_for("clubs"))
    return render_template("player.html", p=p, pr_color=pr_color)


# ── Add player ────────────────────────────────────────────────────────────────

@app.route("/player/add", methods=["GET", "POST"])
def add_player():
    g = guard()
    if g:
        return g
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").lower().strip().replace(" ", "")
        if "$" in name:
            flash("Player name cannot contain $. Use S instead.", "danger")
        else:
            f = request.form
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM player WHERE name = %s", (name,))
                if cur.fetchone():
                    flash(f"Player '{name}' already exists.", "danger")
                else:
                    try:
                        club_name = f.get("club_name", "no club").lower()
                        cur.execute("SELECT club_name FROM club WHERE club_name = %s", (club_name,))
                        if not cur.fetchone() and club_name != "no club":
                            cur.execute("INSERT INTO club (club_name) VALUES (%s)", (club_name,))
                        cur.execute("""
                            INSERT INTO player (
                                name, club_name,
                                sp1_name, sp1_skills, sp2_name, sp2_skills,
                                sp3_name, sp3_skills, sp4_name, sp4_skills,
                                sp5_name, sp5_skills,
                                nerf, pr, team_name, charbats, toolbats, source,
                                last_updated, nerf_updated
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                      CURRENT_DATE, CURRENT_DATE)
                        """, (
                            name, club_name,
                            f.get("sp1_name", ""), f.get("sp1_skills", ""),
                            f.get("sp2_name", ""), f.get("sp2_skills", ""),
                            f.get("sp3_name", ""), f.get("sp3_skills", ""),
                            f.get("sp4_name", ""), f.get("sp4_skills", ""),
                            f.get("sp5_name", ""), f.get("sp5_skills", ""),
                            f.get("nerf", ""),
                            int(f.get("pr") or 9999),
                            f.get("team_name", ""),
                            int(f.get("charbats") or 0),
                            int(f.get("toolbats") or 0),
                            f.get("source", ""),
                        ))
                        conn.commit()
                        conn.close()
                        flash(f"Added player '{name}'.", "success")
                        return redirect(url_for("player_detail", player_name=name))
                    except Exception as e:
                        conn.rollback()
                        flash(f"Error: {e}", "danger")

    with conn.cursor() as cur:
        cur.execute("SELECT club_name FROM club ORDER BY club_name")
        club_list = [r[0] for r in cur.fetchall()]
    conn.close()
    return render_template("add_player.html", clubs=club_list)


# ── Edit player ───────────────────────────────────────────────────────────────

@app.route("/player/<player_name>/edit", methods=["GET", "POST"])
def edit_player(player_name):
    g = guard()
    if g:
        return g
    conn = get_db()

    if request.method == "POST":
        f = request.form
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE player SET
                        club_name=%s,
                        sp1_name=%s, sp1_skills=%s,
                        sp2_name=%s, sp2_skills=%s,
                        sp3_name=%s, sp3_skills=%s,
                        sp4_name=%s, sp4_skills=%s,
                        sp5_name=%s, sp5_skills=%s,
                        nerf=%s, pr=%s, team_name=%s,
                        charbats=%s, toolbats=%s, source=%s,
                        last_updated=CURRENT_DATE
                    WHERE name=%s
                """, (
                    f.get("club_name", "").lower(),
                    f.get("sp1_name", ""), f.get("sp1_skills", ""),
                    f.get("sp2_name", ""), f.get("sp2_skills", ""),
                    f.get("sp3_name", ""), f.get("sp3_skills", ""),
                    f.get("sp4_name", ""), f.get("sp4_skills", ""),
                    f.get("sp5_name", ""), f.get("sp5_skills", ""),
                    f.get("nerf", ""),
                    int(f.get("pr") or 9999),
                    f.get("team_name", ""),
                    int(f.get("charbats") or 0),
                    int(f.get("toolbats") or 0),
                    f.get("source", ""),
                    player_name,
                ))
            conn.commit()
            conn.close()
            flash("Player updated.", "success")
            return redirect(url_for("player_detail", player_name=player_name))
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}", "danger")

    with conn.cursor() as cur:
        p = fetch_one_dict(cur, """
            SELECT name, club_name, sp1_name, sp1_skills, sp2_name, sp2_skills,
                   sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name, sp5_skills,
                   nerf, pr, last_updated, nerf_updated, team_name, charbats, toolbats, source
            FROM player WHERE name = %s
        """, (player_name,))
        cur.execute("SELECT club_name FROM club ORDER BY club_name")
        club_list = [r[0] for r in cur.fetchall()]
    conn.close()

    if not p:
        flash(f"Player '{player_name}' not found.", "warning")
        return redirect(url_for("clubs"))
    return render_template("edit_player.html", p=p, clubs=club_list)


# ── Delete player ─────────────────────────────────────────────────────────────

@app.route("/player/<player_name>/delete", methods=["POST"])
def delete_player(player_name):
    g = guard()
    if g:
        return g
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM player WHERE name = %s", (player_name,))
        conn.commit()
        flash(f"Deleted '{player_name}'.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    conn.close()
    return redirect(url_for("clubs"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

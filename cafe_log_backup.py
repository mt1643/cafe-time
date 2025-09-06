import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

DB_NAME = "cafe_log.db"
HOURLY_RATE = 500  # 1時間あたりのカフェ代（円）

# DB初期化
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY,
                    start_time TEXT,
                    end_time TEXT,
                    duration_minutes INTEGER,
                    cost INTEGER)''')
    conn.commit()
    conn.close()

# 作業開始
def start_session():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO logs (start_time) VALUES (?)", (now,))
    conn.commit()
    conn.close()
    messagebox.showinfo("開始", f"作業開始: {now}")

# 作業終了
def end_session():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 最新の未終了セッションを探す
    c.execute("SELECT id, start_time FROM logs WHERE end_time IS NULL ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    if row:
        log_id, start_time_str = row
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        duration = int((now - start_time).total_seconds() / 60)
        cost = int((duration / 60) * HOURLY_RATE)

        c.execute("UPDATE logs SET end_time=?, duration_minutes=?, cost=? WHERE id=?",
                  (now_str, duration, cost, log_id))
        conn.commit()
        messagebox.showinfo("終了", f"作業終了: {now_str}\n時間: {duration}分\n金額: {cost}円")
    else:
        messagebox.showwarning("警告", "開始していません！")
    conn.close()

# 月集計
def monthly_summary():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    month_prefix = datetime.now().strftime("%Y-%m")
    c.execute("SELECT SUM(duration_minutes), SUM(cost) FROM logs WHERE start_time LIKE ?", (f"{month_prefix}%",))
    total_minutes, total_cost = c.fetchone()
    total_minutes = total_minutes or 0
    total_cost = total_cost or 0
    messagebox.showinfo("今月の集計", f"合計時間: {total_minutes}分\n合計金額: {total_cost}円")
    conn.close()

# GUI
init_db()
root = tk.Tk()
root.title("カフェ作業ログ")

tk.Button(root, text="開始", command=start_session, width=20).pack(pady=5)
tk.Button(root, text="終了", command=end_session, width=20).pack(pady=5)
tk.Button(root, text="今月の集計", command=monthly_summary, width=20).pack(pady=5)

root.mainloop()

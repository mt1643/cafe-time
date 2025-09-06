import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

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

# 日別作業時間グラフ
def show_daily_chart():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 過去30日間のデータを取得
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    c.execute("""
        SELECT DATE(start_time) as date, SUM(duration_minutes) as total_minutes
        FROM logs 
        WHERE start_time >= ? AND end_time IS NOT NULL
        GROUP BY DATE(start_time)
        ORDER BY date
    """, (start_date.strftime("%Y-%m-%d"),))
    
    data = c.fetchall()
    conn.close()
    
    if not data:
        messagebox.showinfo("情報", "表示するデータがありません")
        return
    
    # グラフ作成
    fig, ax = plt.subplots(figsize=(10, 6))
    dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in data]
    minutes = [row[1] for row in data]
    
    ax.plot(dates, minutes, marker='o', linewidth=2, markersize=6, color='#2E86AB')
    ax.set_title('過去30日間の作業時間推移', fontsize=14, fontweight='bold')
    ax.set_xlabel('日付', fontsize=12)
    ax.set_ylabel('作業時間（分）', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # 日付フォーマット
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # 新しいウィンドウで表示
    chart_window = tk.Toplevel(root)
    chart_window.title("作業時間推移グラフ")
    
    canvas = FigureCanvasTkAgg(fig, chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# 月別集計グラフ
def show_monthly_chart():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 過去12ヶ月のデータを取得
    c.execute("""
        SELECT strftime('%Y-%m', start_time) as month, 
               SUM(duration_minutes) as total_minutes,
               SUM(cost) as total_cost
        FROM logs 
        WHERE end_time IS NOT NULL
        GROUP BY strftime('%Y-%m', start_time)
        ORDER BY month DESC
        LIMIT 12
    """)
    
    data = c.fetchall()
    conn.close()
    
    if not data:
        messagebox.showinfo("情報", "表示するデータがありません")
        return
    
    # データを逆順にして古い順に
    data.reverse()
    
    # グラフ作成
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    months = [row[0] for row in data]
    minutes = [row[1] for row in data]
    costs = [row[2] for row in data]
    
    # 作業時間グラフ
    ax1.bar(months, minutes, color='#A23B72', alpha=0.7)
    ax1.set_title('月別作業時間', fontsize=14, fontweight='bold')
    ax1.set_ylabel('作業時間（分）', fontsize=12)
    ax1.grid(True, alpha=0.3, axis='y')
    plt.setp(ax1.get_xticklabels(), rotation=45)
    
    # 費用グラフ
    ax2.bar(months, costs, color='#F18F01', alpha=0.7)
    ax2.set_title('月別カフェ代', fontsize=14, fontweight='bold')
    ax2.set_xlabel('月', fontsize=12)
    ax2.set_ylabel('金額（円）', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    plt.setp(ax2.get_xticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # 新しいウィンドウで表示
    chart_window = tk.Toplevel(root)
    chart_window.title("月別集計グラフ")
    
    canvas = FigureCanvasTkAgg(fig, chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# GUI
init_db()
root = tk.Tk()
root.title("カフェ作業ログ")

tk.Button(root, text="開始", command=start_session, width=20).pack(pady=5)
tk.Button(root, text="終了", command=end_session, width=20).pack(pady=5)
tk.Button(root, text="今月の集計", command=monthly_summary, width=20).pack(pady=5)
tk.Button(root, text="日別グラフ", command=show_daily_chart, width=20).pack(pady=5)
tk.Button(root, text="月別グラフ", command=show_monthly_chart, width=20).pack(pady=5)

root.mainloop()
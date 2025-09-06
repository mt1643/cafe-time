import os
# macOSのダークモードを無効にする複数の方法
os.environ['TK_SILENCE_DEPRECATION'] = '1'
os.environ['TKINTER_DARK_MODE'] = '0'
os.environ['_TKINTER_DARK_MODE'] = '0'
os.environ['TKINTER_APPEARANCE'] = 'light'
os.environ['_TKINTER_APPEARANCE'] = 'light'

# macOSの外観設定を強制的にライトモードに変更
try:
    import subprocess
    subprocess.run(['defaults', 'write', '-g', 'AppleInterfaceStyle', '-string', 'Light'], 
                   capture_output=True, check=False)
except:
    pass

import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import matplotlib.font_manager as fm

# 日本語フォント設定（利用可能なフォントのみ）
plt.rcParams['font.family'] = ['Hiragino Sans', 'YuGothic', 'Apple SD Gothic Neo', 'AppleGothic', 'BIZ UDGothic']
plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化けを防ぐ

DB_NAME = "cafe_log.db"
DEFAULT_HOURLY_RATE = 500  # デフォルトの1時間あたりのカフェ代（円）

# picディレクトリの作成
PIC_DIR = "pic"
if not os.path.exists(PIC_DIR):
    os.makedirs(PIC_DIR)

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

# カフェ代入力ダイアログ（超強制ライトモード版）
def get_cafe_cost(duration_minutes, default_cost):
    # 新しいルートウィンドウを作成
    dialog = tk.Tk()
    dialog.title("カフェ代入力")
    dialog.geometry("600x350")
    dialog.resizable(False, False)
    
    # 強制的にライトモードの色を設定
    dialog.configure(bg="white")
    
    # 中央に配置
    dialog.geometry("+%d+%d" % (root.winfo_rootx() + 100, root.winfo_rooty() + 100))
    
    result = {"cost": None}
    
    # メインフレーム
    main_frame = tk.Frame(dialog, padx=50, pady=50, bg="white")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 作業時間表示
    duration_hours = duration_minutes / 60
    time_label = tk.Label(main_frame, text=f"作業時間: {duration_minutes}分 ({duration_hours:.1f}時間)", 
                         font=("Arial", 16, "bold"), bg="white", fg="black")
    time_label.pack(pady=(0, 25))
    
    # 金額入力ラベル
    cost_label = tk.Label(main_frame, text="カフェ代を入力してください（円）:", 
                         font=("Arial", 14), bg="white", fg="black")
    cost_label.pack(pady=(0, 15))
    
    # 入力フィールド用のフレーム
    entry_frame = tk.Frame(main_frame, bg="white")
    entry_frame.pack(pady=(0, 25))
    
    # 金額入力フィールド（超強制的に白背景）
    cost_var = tk.StringVar(value=str(default_cost))
    cost_entry = tk.Entry(entry_frame, textvariable=cost_var, 
                         font=("Arial", 20, "bold"), width=10,
                         bg="white", fg="black", 
                         insertbackground="black", 
                         relief="solid", bd=4,
                         highlightthickness=4,
                         highlightcolor="blue",
                         highlightbackground="gray",
                         justify="center")
    cost_entry.pack()
    
    # 入力値の確認表示
    def update_preview(*args):
        try:
            value = cost_var.get()
            preview_label.config(text=f"入力値: {value}円", fg="blue")
        except:
            preview_label.config(text="入力値: エラー", fg="red")
    
    cost_var.trace('w', update_preview)
    preview_label = tk.Label(main_frame, text=f"入力値: {default_cost}円", 
                            font=("Arial", 14), bg="white", fg="blue")
    preview_label.pack(pady=(0, 25))
    
    # ボタンフレーム
    button_frame = tk.Frame(main_frame, bg="white")
    button_frame.pack()
    
    def ok_clicked():
        try:
            cost = int(cost_var.get())
            if 0 <= cost <= 10000:
                result["cost"] = cost
                dialog.quit()
            else:
                messagebox.showerror("エラー", "金額は0円以上10,000円以下で入力してください")
        except ValueError:
            messagebox.showerror("エラー", "正しい数値を入力してください")
    
    def cancel_clicked():
        dialog.quit()
    
    # OKボタン
    ok_button = tk.Button(button_frame, text="OK", command=ok_clicked, 
                         width=15, bg="blue", fg="white", font=("Arial", 14, "bold"),
                         relief="flat", bd=0, padx=20, pady=10)
    ok_button.pack(side=tk.LEFT, padx=(0, 20))
    
    # キャンセルボタン
    cancel_button = tk.Button(button_frame, text="キャンセル", command=cancel_clicked, 
                             width=15, font=("Arial", 14), bg="lightgray", fg="black",
                             relief="flat", bd=0, padx=20, pady=10)
    cancel_button.pack(side=tk.LEFT)
    
    # EnterキーでOK
    def on_enter(event):
        ok_clicked()
    
    cost_entry.bind('<Return>', on_enter)
    
    # フォーカスを設定
    cost_entry.focus()
    cost_entry.select_range(0, tk.END)
    
    # ダイアログが閉じられるまで待機
    dialog.mainloop()
    
    # 結果を取得してダイアログを破棄
    cost = result["cost"]
    dialog.destroy()
    
    return cost

# カフェ代入力（ターミナル版）
def get_cafe_cost_terminal(duration_minutes, default_cost):
    print(f"\n=== カフェ代入力 ===")
    print(f"作業時間: {duration_minutes}分 ({duration_minutes/60:.1f}時間)")
    print(f"デフォルト金額: {default_cost}円")
    
    while True:
        try:
            user_input = input(f"カフェ代を入力してください（円）[{default_cost}]: ").strip()
            
            if user_input == "":
                return default_cost
            
            cost = int(user_input)
            if 0 <= cost <= 10000:
                return cost
            else:
                print("エラー: 金額は0円以上10,000円以下で入力してください")
        except ValueError:
            print("エラー: 正しい数値を入力してください")
        except KeyboardInterrupt:
            print("\nキャンセルされました")
            return None

# 作業終了（改良版）
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
        
        # カフェ代の金額を入力
        duration_hours = duration / 60
        default_cost = int(duration_hours * DEFAULT_HOURLY_RATE)
        
        # まずGUIダイアログを試す
        try:
            cost = get_cafe_cost(duration, default_cost)
        except Exception as e:
            print(f"GUIダイアログエラー: {e}")
            # GUIダイアログが失敗した場合はターミナルで入力
            cost = get_cafe_cost_terminal(duration, default_cost)
        
        if cost is None:  # キャンセルされた場合
            conn.close()
            return
        
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
    
    # 棒グラフに変更
    ax.bar(dates, minutes, color='#2E86AB', alpha=0.7, width=0.8)
    ax.set_title('過去30日間の作業時間推移', fontsize=14, fontweight='bold')
    ax.set_xlabel('日付', fontsize=12)
    ax.set_ylabel('作業時間（分）', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    # 日付フォーマット
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # ファイルに保存して開く
    filename = os.path.join(PIC_DIR, "daily_chart.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()  # メモリを解放
    
    # デフォルトアプリケーションで開く
    import subprocess
    import platform
    if platform.system() == 'Darwin':  # macOS
        subprocess.run(['open', filename])
    elif platform.system() == 'Windows':
        subprocess.run(['start', filename], shell=True)
    else:  # Linux
        subprocess.run(['xdg-open', filename])
    
    messagebox.showinfo("完了", f"グラフを保存しました: {filename}")

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
    
    # ファイルに保存して開く
    filename = os.path.join(PIC_DIR, "monthly_chart.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()  # メモリを解放
    
    # デフォルトアプリケーションで開く
    import subprocess
    import platform
    if platform.system() == 'Darwin':  # macOS
        subprocess.run(['open', filename])
    elif platform.system() == 'Windows':
        subprocess.run(['start', filename], shell=True)
    else:  # Linux
        subprocess.run(['xdg-open', filename])
    
    messagebox.showinfo("完了", f"グラフを保存しました: {filename}")

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
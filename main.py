import sqlite3  # 1. SQLite3データベースを操作するライブラリをインポート
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
DB_NAME = "todo.db"  # 2. データベースの保存ファイル名を指定


# 【解説】データベースとテーブル（データの保管棚）を初期化する関数
def init_db():
    # sqlite3.connect でデータベースファイルに接続（なければ自動作成）
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()  # SQL命令を実行するための「カーソル」を作成

    # tasks という名前のテーブル（表）を作るSQL命令
    # id: 自動で増える背番号（これでタスクがズレるバグが消える！）
    # content: タスクの本文（テキスト形式）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    """)
    conn.commit()  # 変更を確定させる
    conn.close()  # 接続を閉じる


# トップページ（一覧表示と追加）
@app.route("/", methods=["GET", "POST"])
def todo_app():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. 【Create】追加ボタンが押された場合
    if request.method == "POST":
        task = request.form.get("task_content")
        if task:
            # SQLの INSERT 命令で、tasksテーブルにタスクを安全に保存
            cursor.execute("INSERT INTO tasks (content) VALUES (?)", (task,))
            conn.commit()
        conn.close()
        return redirect(url_for("todo_app"))

    # 2. 【Read】通常アクセス時：タスク一覧をすべて取得
    # SELECT id, content で、背番号と本文をまとめて取得する
    cursor.execute("SELECT id, content FROM tasks")
    tasks_data = (
        cursor.fetchall()
    )  # 取得したデータをリスト形式 [ (1, '買い物'), (2, '勉強') ] で全回収
    conn.close()

    return render_template("todo.html", tasks=tasks_data)


# 【Delete】削除処理
# URLパラメータで、リストの順番ではなく、データベースの「固定されたid」を受け取る
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # SQLの DELETE 命令で、指定されたidの行をピンポイントで削除
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("todo_app"))


# 【Update】編集処理
@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if request.method == "POST":
        new_task = request.form.get("updated_content")
        if new_task:
            # SQLの UPDATE 命令で、指定されたidのタスク内容を書き換える
            cursor.execute(
                "UPDATE tasks SET content = ? WHERE id = ?",
                (new_task, task_id),
            )
            conn.commit()
        conn.close()
        return redirect(url_for("todo_app"))

    # 最初画面を開いたとき：指定されたidのタスクを1件だけ取得
    cursor.execute("SELECT content FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()  # 1件だけ回収
    conn.close()

    if task is None:
        return redirect(url_for("todo_app"))

    return render_template("edit.html", current_task=task[0], task_id=task_id)


if __name__ == "__main__":
    init_db()  # アプリ起動時に、最初にデータベースの準備を行う
    app.run(debug=True)

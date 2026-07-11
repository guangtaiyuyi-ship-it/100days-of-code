from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy  # 1. ORM（SQLAlchemy）の道具箱をインポート

app = Flask(__name__)

# 2. データベースの接続先を設定（sqliteを指定。アプリと同じ場所に todo.db を作る）
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
# 3. データベース操作中に裏側でどんなSQLが動いているかをターミナルに表示する設定（学習に便利！）
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 4. FlaskアプリとORMを合体させて、データベース操作の司令塔「db」を作成
db = SQLAlchemy(app)


# ==================== 【解説】テーブルの定義 ====================
# SQL文を使わず、Pythonのクラスを使って「保存するデータの形」を定義します
class TodoTask(db.Model):
    __tablename__ = "tasks"  # データベース内での実際のテーブル名を「tasks」に指定

    # 列の定義：id（自動で増える背番号）
    id = db.Column(db.Integer, primary_key=True)
    # 列の定義：content（タスクの本文。文字数は最大200文字、空っぽは禁止）
    content = db.Column(db.String(200), nullable=False)


# ==================== メインの処理 ====================


# トップページ（一覧表示と追加）
@app.route("/", methods=["GET", "POST"])
def todo_app():
    # 1. 【Create】追加ボタンが押された場合
    if request.method == "POST":
        task_text = request.form.get("task_content")
        if task_text:
            # クラスから新しくタスクのデータ（オブジェクト）を作成
            new_task = TodoTask(content=task_text)
            db.session.add(new_task)  # データベースの「追加予定リスト」に入れる
            db.session.commit()  # 変更を確定（保存）する
        return redirect(url_for("todo_app"))

    # 2. 【Read】通常アクセス時：タスク一覧をすべて取得
    # SQL文（SELECT * FROM tasks）の代わりに、これだけで全件取得できます
    # データの形式も自動的に調整されるため、HTML（todo.html）側の書き換えは不要です
    tasks_data = TodoTask.query.all()
    return render_template("todo.html", tasks=tasks_data)


# 【Delete】削除処理
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    # 指定されたIDのタスクをデータベースから1件だけ検索して取得
    task = TodoTask.query.get_or_404(task_id)
    db.session.delete(task)  # 取得したタスクを削除
    db.session.commit()  # 変更を確定
    return redirect(url_for("todo_app"))


# 【Update】編集処理
@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    # 指定されたIDのタスクを1件取得（なければ404エラー画面を自動で出す安全設計）
    task = TodoTask.query.get_or_404(task_id)

    if request.method == "POST":
        new_text = request.form.get("updated_content")
        if new_text:
            task.content = new_text  # Pythonの変数の中身を書き換えるだけで...
            db.session.commit()  # 裏側で自動的にUPDATE文が作られて保存される！
        return redirect(url_for("todo_app"))

    # 最初画面を開いたとき：現在の文字（task.content）とIDをHTMLに渡す
    return render_template("edit.html", current_task=task.content, task_id=task_id)


if __name__ == "__main__":
    # アプリ起動時に、上で定義したテーブル（TodoTask）をデータベース内に自動作成する
    with app.app_context():
        db.create_all()

    app.run(debug=True)

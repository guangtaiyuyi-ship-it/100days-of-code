from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 【重要】セッション（ログイン情報の暗号化鍵）の偽造を防ぐための秘密のパスワード
# 本番では推測されにくい長いランダムな文字列にします
app.secret_key = "super-secret-key-abcde"

db = SQLAlchemy(app)


# ==================== データベースの定義 ====================


# 1. ユーザー情報を保存するテーブル
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # パスワードはそのまま保存せず、暗号化後の長い文字列（ハッシュ）が入るようにします
    password_hash = db.Column(db.String(200), nullable=False)

    # ユーザーとタスクの紐付け（1対多のリレーションシップ）
    # user.tasks と書くだけで、そのユーザーの全タスクを引き出せるようになります
    tasks = db.relationship("TodoTask", backref="owner", lazy=True)


# 2. タスク情報を保存するテーブル
class TodoTask(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)

    # 【重要】誰のタスクかを記録する列。usersテーブルのidとリンクさせます（外部キー）
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


# ==================== ルーティング（各画面の処理） ====================


# ユーザー登録（サインアップ）
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # 既に同じ名前のユーザーが登録されていないかチェック
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "そのユーザー名は既に使われています", 400

        if username and password:
            # パスワードを安全にハッシュ化（暗号化）
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_pw)

            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))

    return render_template("signup.html")


# ログイン画面
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        # ユーザーが存在し、かつ入力されたパスワードがハッシュ値と一致するか検証
        if user and check_password_hash(user.password_hash, password):
            # 合言葉が一致したら、セッション（サーバー側の記憶）にユーザーIDを保存
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("todo_app"))

        return "ユーザー名またはパスワードが間違っています", 401

    return render_template("login.html")


# ログアウト処理
@app.route("/logout")
def logout():
    session.clear()  # セッションの記憶をすべて消去してログアウト状態にする
    return redirect(url_for("login"))


# メインのTodoリスト画面
@app.route("/", methods=["GET", "POST"])
def todo_app():
    # 【ログインチェック】セッションにIDがなければ、ログイン画面へ強制送還
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        task_text = request.form.get("task_content")
        if task_text:
            # 現在ログインしている人のID（session['user_id']）を紐付けてタスクを保存
            new_task = TodoTask(content=task_text, user_id=session["user_id"])
            db.session.add(new_task)
            db.session.commit()
        return redirect(url_for("todo_app"))

    # 【重要】すべてのタスクではなく、「現在ログイン中のユーザーのタスク」だけを絞り込んで取得
    tasks_data = TodoTask.query.filter_by(user_id=session["user_id"]).all()
    return render_template("todo.html", tasks=tasks_data, username=session["username"])


# 一括削除・単体削除・編集の処理（すべての関数でログインチェックが必要です）
@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    task = TodoTask.query.get_or_404(task_id)
    # 他人のタスクを操作できないようにガードをかける（セキュリティ対策）
    if task.user_id != session["user_id"]:
        return "権限がありません", 403

    task.is_completed = not task.is_completed
    db.session.commit()
    return redirect(url_for("todo_app"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    task = TodoTask.query.get_or_404(task_id)
    if task.user_id != session["user_id"]:
        return "権限がありません", 403

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("todo_app"))


@app.route("/delete_completed", methods=["POST"])
def delete_completed_tasks():
    if "user_id" not in session:
        return redirect(url_for("login"))
    # 自分のタスク、かつ完了済みのものだけを一括抽出
    completed_tasks = TodoTask.query.filter_by(
        user_id=session["user_id"], is_completed=True
    ).all()
    for task in completed_tasks:
        db.session.delete(task)
    db.session.commit()
    return redirect(url_for("todo_app"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    task = TodoTask.query.get_or_404(task_id)
    if task.user_id != session["user_id"]:
        return "権限がありません", 403

    if request.method == "POST":
        new_text = request.form.get("updated_content")
        if new_text:
            task.content = new_text
            db.session.commit()
        return redirect(url_for("todo_app"))
    return render_template("edit.html", current_task=task.content, task_id=task_id)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = "super-secret-key-abcde"

db = SQLAlchemy(app)

# ==================== データベースの定義 ====================

# 1. ユーザー情報を保存するテーブル
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    books = db.relationship("Book", backref="owner", lazy=True)

# 2. 書籍情報を保存するテーブル
class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
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
            return redirect(url_for("list_app"))

        return "ユーザー名またはパスワードが間違っています", 401

    return render_template("login.html")


# ログアウト処理
@app.route("/logout")
def logout():
    session.clear()  # セッションの記憶をすべて消去してログアウト状態にする
    return redirect(url_for("login"))


# メイン画面
@app.route("/", methods=["GET", "POST"])
def list_app():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        book_title = request.form.get("book_title")
        author = request.form.get("author")
        if book_title and author:
            # 現在ログインしている人のID（session['user_id']）を紐付けてタスクを保存
            new_book = Book(title=book_title, author=author, user_id=session["user_id"])
            db.session.add(new_book)
            db.session.commit()
        return redirect(url_for("list_app"))

    # 【重要】すべての書籍リストではなく、「現在ログイン中のユーザーの書籍」だけを絞り込んで取得
    book_data = Book.query.filter_by(user_id=session["user_id"]).all()
    return render_template("books.html", books=book_data, username=session["username"])


# 一括削除・単体削除・編集の処理（すべての関数でログインチェックが必要です）
@app.route("/toggle/<int:book_id>", methods=["POST"])
def toggle_books(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    book = Book.query.get_or_404(book_id)
    # 他人のリストを操作できないようにガードをかける（セキュリティ対策）
    if book.user_id != session["user_id"]:
        return "権限がありません", 403

    book.is_completed = not book.is_completed
    db.session.commit()
    return redirect(url_for("list_app"))


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    book = Book.query.get_or_404(book_id)
    if book.user_id != session["user_id"]:
        return "権限がありません", 403

    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("list_app"))


@app.route("/delete_completed", methods=["POST"])
def delete_completed_books():
    if "user_id" not in session:
        return redirect(url_for("login"))
    # 自分の書籍、かつ読了済みのものだけを一括抽出
    completed_books = Book.query.filter_by(
        user_id=session["user_id"], is_completed=True
    ).all()
    for book in completed_books:
        db.session.delete(book)
    db.session.commit()
    return redirect(url_for("list_app"))


@app.route("/edit/<int:book_id>", methods=["GET", "POST"])
def edit_books(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    book = Book.query.get_or_404(book_id)
    if book.user_id != session["user_id"]:
        return "権限がありません", 403

    if request.method == "POST":
        new_title = request.form.get("updated_title")
        new_author = request.form.get("updated_author")
        if new_title:
            book.title = new_title
        if new_author:
            book.author = new_author
        db.session.commit()
        return redirect(url_for("list_app"))
    return render_template("edit.html", current_book=book.title, current_author=book.author, book_id=book_id)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

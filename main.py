from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ==================== 【解説】テーブル定義の変更 ====================
class TodoTask(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

    # 【新規追加】完了状態を保存する列（Boolean型：真偽値）。初期値は「未完了（False）」
    is_completed = db.Column(db.Boolean, default=False, nullable=False)


@app.route("/", methods=["GET", "POST"])
def todo_app():
    if request.method == "POST":
        task_text = request.form.get("task_content")
        if task_text:
            # 新規追加時は is_completed は自動的に False（未完了）になります
            new_task = TodoTask(content=task_text)
            db.session.add(new_task)
            db.session.commit()
        return redirect(url_for("todo_app"))

    tasks_data = TodoTask.query.all()
    return render_template("todo.html", tasks=tasks_data)


# ==================== 【新規追加】完了・未完了の切り替え処理 ====================
@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    # 指定されたIDのタスクを取得
    task = TodoTask.query.get_or_404(task_id)

    # 【解説】現在の状態を反転させる（TrueならFalseに、FalseならTrueにする）
    task.is_completed = not task.is_completed

    db.session.commit()  # データベースに変更を保存
    return redirect(url_for("todo_app"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    task = TodoTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("todo_app"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = TodoTask.query.get_or_404(task_id)
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

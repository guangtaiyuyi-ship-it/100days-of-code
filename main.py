import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

TXT_FILE = "tasks.txt"


def load_tasks():
    if not os.path.exists(TXT_FILE):
        return [] 
    with open(TXT_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_tasks(tasks):
    with open(TXT_FILE, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(f"{task}\n")  

@app.route("/", methods=["GET", "POST"])
def todo_app():
    tasks = load_tasks() 

    if request.method == "POST":
        task = request.form.get("task_content")
        if task:
            tasks.append(task)  
            save_tasks(tasks)  
        return redirect(url_for("todo_app"))

    return render_template("todo.html", tasks=tasks)

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    tasks = load_tasks()  

    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)  
        save_tasks(tasks)  
    return redirect(url_for("todo_app")) 


if __name__ == "__main__":
    app.run(debug=True)

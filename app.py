from flask import Flask, render_template, request, redirect, session
import jwt
import datetime
from reportlab.pdfgen import canvas
import sqlite3
app = Flask(__name__)
app.secret_key = "financeflow_secret_key"

@app.route("/logout")
def logout():

    session.pop("token", None)

    return redirect("/login")
# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    return render_template("home.html")

# =========================
# LOGIN PAGE
# =========================
@app.route("/login")
def login():
    return render_template("login.html")
# =========================
# SIGNUP PAGE
# =========================
@app.route("/signup")
def signup():
    return render_template("signup.html")
# =========================
# REGISTER USER
# =========================
@app.route("/register", methods=["POST"])
def register():

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    try:

        cursor.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, password)
        )

        conn.commit()

    except:
        conn.close()
        return "Email already registered"

    conn.close()

    return redirect("/login")


# =========================
# LOGIN CHECK
# =========================
@app.route("/check_login", methods=["POST"])
def check_login():
    print("CHECK LOGIN CALLED")

    email = request.form["email"]
    password = request.form["password"]
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        token = jwt.encode(
            {
                "email": email,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            app.secret_key,
            algorithm="HS256"
        )

        session["token"] = token

        print("LOGIN SUCCESS")
        print(token)

        return redirect("/dashboard")

    else:
        return "Invalid Email or Password"
# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():

    token = session.get("token")

    if not token:
        return redirect("/login")

    try:
        jwt.decode(
            token,
            app.secret_key,
            algorithms=["HS256"]
        )
    except:
        return redirect("/login")

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    # Total Income
    cursor.execute("SELECT SUM(amount) FROM income")
    total_income = cursor.fetchone()[0]

    if total_income is None:
        total_income = 0

    # Total Expense
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expense = cursor.fetchone()[0]

    if total_expense is None:
        total_expense = 0

    balance = total_income - total_expense

    # Recent Expenses
    cursor.execute(
        "SELECT category, amount FROM expenses ORDER BY id DESC LIMIT 10"
    )

    transactions = cursor.fetchall()

    # Chart Data
    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        GROUP BY category
    """)

    chart_data = cursor.fetchall()

    labels = []
    values = []

    for row in chart_data:
        labels.append(row[0])
        values.append(row[1])

    conn.close()

    return render_template(
        "dashboard.html",
        income=total_income,
        expense=total_expense,
        balance=balance,
        transactions=transactions,
        labels=labels,
        values=values
    )
# =========================
# ADD EXPENSE
# =========================
@app.route("/add_expense", methods=["POST"])
def add_expense():

    category = request.form["category"]
    amount = request.form["amount"]

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO expenses(category,amount,date) VALUES(?,?,?)",
        (category, amount, "2026-06-16")
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")
# =========================
# EXPENSE HISTORY
# =========================
@app.route("/expenses")
def expenses():

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, category, amount, date FROM expenses ORDER BY id DESC"
    )

    expense_data = cursor.fetchall()

    conn.close()

    return render_template(
        "expenses.html",
        expenses=expense_data
    )
# =========================
# DELETE EXPENSE
# =========================
@app.route("/delete_expense/<int:id>")
def delete_expense(id):

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/expenses")
# =========================
# ADD INCOME
# =========================
@app.route("/add_income", methods=["POST"])
def add_income():

    source = request.form["source"]
    amount = request.form["amount"]

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO income(source,amount) VALUES(?,?)",
        (source, amount)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")
# =========================
# INCOME HISTORY
# =========================
@app.route("/income")
def income():

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, source, amount FROM income ORDER BY id DESC"
    )

    income_data = cursor.fetchall()

    conn.close()

    return render_template(
        "income.html",
        incomes=income_data
    )
# =========================
# USERS
# =========================
@app.route("/users")
def users():

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")

    users_data = cursor.fetchall()

    conn.close()

    return str(users_data)
# =========================
# PDF REPORT
# =========================
@app.route("/download_report")
def download_report():

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM income")
    income = cursor.fetchone()[0]

    if income is None:
        income = 0

    cursor.execute("SELECT SUM(amount) FROM expenses")
    expense = cursor.fetchone()[0]

    if expense is None:
        expense = 0

    balance = income - expense

    conn.close()

    pdf = canvas.Canvas("finance_report.pdf")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(180, 800, "FinanceFlow Report")

    pdf.setFont("Helvetica", 14)
    pdf.drawString(100, 700, f"Total Income : Rs {income}")
    pdf.drawString(100, 650, f"Total Expense : Rs {expense}")
    pdf.drawString(100, 600, f"Balance : Rs {balance}")

    pdf.save()

    return "PDF Report Created Successfully"
# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
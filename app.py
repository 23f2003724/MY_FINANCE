import os
from contextlib import contextmanager
from datetime import date, datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy import Float, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

MONTHLY_BUDGET = 3000.0
DAILY_LIMIT = 100.0


def normalize_database_url(raw_url):
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


DATABASE_URL = normalize_database_url(
    os.environ.get("DATABASE_URL", "sqlite:///database.db")
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    DATABASE_URL, connect_args=connect_args, pool_pre_ping=True, future=True
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    item: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def parse_date(date_text):
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_float(value):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def to_money(value):
    return round(float(value or 0.0), 2)


@app.route("/")
def index():
    today = date.today().isoformat()

    with get_session() as session:
        daily_rows_raw = (
            session.query(
                Expense.date.label("date"),
                func.coalesce(func.round(func.sum(Expense.amount), 2), 0.0).label("total"),
            )
            .group_by(Expense.date)
            .order_by(Expense.date.desc())
            .all()
        )

        recent_expense_rows = (
            session.query(Expense)
            .order_by(Expense.date.desc(), Expense.id.desc())
            .limit(15)
            .all()
        )

        total_spent = to_money(
            session.query(func.coalesce(func.sum(Expense.amount), 0.0)).scalar()
        )
        today_total = to_money(
            session.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(Expense.date == today)
            .scalar()
        )

    daily_rows = []
    shopping_balance = 0.0
    for row in daily_rows_raw:
        day_total = to_money(row.total)
        day_saved = to_money(max(0.0, DAILY_LIMIT - day_total))
        day_extra = to_money(max(0.0, day_total - DAILY_LIMIT))
        shopping_balance = to_money(shopping_balance + day_saved)
        daily_rows.append(
            {
                "date": row.date,
                "total": day_total,
                "saved": day_saved,
                "extra": day_extra,
                "is_over": day_total > DAILY_LIMIT,
            }
        )

    recent_expenses = [
        {
            "id": row.id,
            "date": row.date,
            "item": row.item,
            "amount": to_money(row.amount),
        }
        for row in recent_expense_rows
    ]

    daily_status = "Over budget" if today_total > DAILY_LIMIT else "Saved"
    daily_diff = to_money(abs(today_total - DAILY_LIMIT))

    remaining = to_money(MONTHLY_BUDGET - total_spent)
    monthly_status = "Overused" if remaining < 0 else "Savings"
    monthly_diff = to_money(abs(remaining))

    nearing_limit = DAILY_LIMIT * 0.8 <= today_total <= DAILY_LIMIT

    return render_template(
        "index.html",
        monthly_budget=MONTHLY_BUDGET,
        total_spent=total_spent,
        remaining=remaining,
        monthly_status=monthly_status,
        monthly_diff=monthly_diff,
        today=today,
        today_total=today_total,
        daily_status=daily_status,
        daily_diff=daily_diff,
        daily_rows=daily_rows,
        recent_expenses=recent_expenses,
        daily_limit=DAILY_LIMIT,
        nearing_limit=nearing_limit,
        shopping_balance=shopping_balance,
    )


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    today = date.today()

    if request.method == "POST":
        expense_date = request.form.get("date", "").strip()
        item = request.form.get("item", "").strip()
        amount = get_float(request.form.get("amount"))

        parsed = parse_date(expense_date)

        if not parsed:
            flash("Please enter a valid date (YYYY-MM-DD).", "danger")
            return redirect(url_for("add_expense"))
        if parsed > today:
            flash("Future dates are not allowed.", "danger")
            return redirect(url_for("add_expense"))
        if not item:
            flash("Item name is required.", "danger")
            return redirect(url_for("add_expense"))
        if amount is None or amount < 0:
            flash("Amount must be a valid number.", "danger")
            return redirect(url_for("add_expense"))

        with get_session() as session:
            session.add(Expense(date=expense_date, item=item, amount=amount))
            session.commit()

        flash("Expense added successfully.", "success")
        return redirect(url_for("index"))

    return render_template("add.html", today=today.isoformat())


@app.route("/edit/<expense_date>", methods=["GET", "POST"])
def edit_day(expense_date):
    selected_date = parse_date(expense_date)
    today = date.today()

    if not selected_date:
        flash("Invalid date format.", "danger")
        return redirect(url_for("index"))

    if selected_date > today:
        flash("You cannot edit future days.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        action = request.form.get("action")
        expense_id = parse_int(request.form.get("expense_id"))

        with get_session() as session:
            if action == "update":
                item = request.form.get("item", "").strip()
                amount = get_float(request.form.get("amount"))

                if not item:
                    flash("Item name cannot be empty.", "danger")
                elif amount is None or amount < 0:
                    flash("Amount must be a valid number.", "danger")
                elif expense_id is None:
                    flash("Invalid expense id.", "danger")
                else:
                    expense = (
                        session.query(Expense)
                        .filter(Expense.id == expense_id, Expense.date == expense_date)
                        .first()
                    )
                    if expense:
                        expense.item = item
                        expense.amount = amount
                        session.commit()
                        flash("Expense updated.", "success")
                    else:
                        flash("Expense not found.", "danger")

            elif action == "delete":
                if expense_id is None:
                    flash("Invalid expense id.", "danger")
                else:
                    expense = (
                        session.query(Expense)
                        .filter(Expense.id == expense_id, Expense.date == expense_date)
                        .first()
                    )
                    if expense:
                        session.delete(expense)
                        session.commit()
                        flash("Expense deleted.", "warning")
                    else:
                        flash("Expense not found.", "danger")

            elif action == "add":
                item = request.form.get("new_item", "").strip()
                amount = get_float(request.form.get("new_amount"))

                if not item:
                    flash("Item name is required.", "danger")
                elif amount is None or amount < 0:
                    flash("Amount must be a valid number.", "danger")
                else:
                    session.add(Expense(date=expense_date, item=item, amount=amount))
                    session.commit()
                    flash("Expense added to this day.", "success")

        return redirect(url_for("edit_day", expense_date=expense_date))

    with get_session() as session:
        expenses_raw = (
            session.query(Expense)
            .filter(Expense.date == expense_date)
            .order_by(Expense.id.desc())
            .all()
        )
        daily_total = to_money(
            session.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(Expense.date == expense_date)
            .scalar()
        )

    expenses = [
        {"id": row.id, "item": row.item, "amount": to_money(row.amount)}
        for row in expenses_raw
    ]

    daily_status = "Over budget" if daily_total > DAILY_LIMIT else "Saved"
    daily_diff = to_money(abs(daily_total - DAILY_LIMIT))

    return render_template(
        "edit.html",
        expense_date=expense_date,
        expenses=expenses,
        daily_total=daily_total,
        daily_limit=DAILY_LIMIT,
        daily_status=daily_status,
        daily_diff=daily_diff,
    )


init_db()


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


# Kullanici giris decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)  # normal
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapınız", "danger")
            return redirect(url_for("login"))
    return decorated_function


# kullanici kayit formu

class RegisterForm(Form):
    name = StringField(
        "İsim-Soyisim:", validators=[validators.length(min=4, max=25)])
    username = StringField("Kullanici Adi:", validators=[
                           validators.length(min=5, max=35)])
    email = StringField("Email Adresi:", validators=[validators.Email(
        message="Lütfen geçerli bir email adresi giriniz")])
    password = PasswordField("Parola:", validators=[validators.DataRequired(
        message="Lütfen bir parola belirleyiniz"), validators.EqualTo(fieldname="confirm", message="Parolaniz uyusmuyor")])
    confirm = PasswordField("Parola Doğrula:")


class LoginForm(Form):
    username = StringField("Kullanici Adı:")
    password = PasswordField("Parola:")


# Makale Formu

class ArticleForm(Form):
    title = StringField("Makale Basligi", validators=[
                        validators.Length(min=5, max=100)])
    content = TextAreaField("Makale İçeriği", validators=[
                            validators.Length(min=10)])


app = Flask(__name__)
app.secret_key = "ybblog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "YBBLOG"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/")
def index():
    # articles = [
    #     {"id": 1, "title": "Deneme1", "content": "Deneme1 icerik"},
    #     {"id": 2, "title": "Deneme2", "content": "Deneme2 icerik"},
    #     {"id": 3, "title": "Deneme3", "content": "Deneme3 icerik"}
    # ]
    # return render_template("index.html", articles=articles)
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where AUTHOR = %s"
    result = cursor.execute(sorgu, (session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")


# Kayit olma


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if(request.method == "POST" and form.validate()):
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "insert into USERS (NAME,EMAIL,USERNAME,PASSWORD) values(%s,%s,%s,%s)"
        cursor.execute(sorgu, (name, email, username, password))
        mysql.connection.commit()
        cursor.close()

        flash("Kayıt islemi basarili bir sekilde gerceklesti.", "success")

        return redirect(url_for("login"))

    else:
        return render_template("register.html", form=form)

# login


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if(request.method == "POST"):
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "select * from USERS where USERNAME=%s"
        result = cursor.execute(sorgu, (username,))

        if(result > 0):
            data = cursor.fetchone()
            real_password = data["PASSWORD"]
            if(sha256_crypt.verify(password_entered, real_password)):
                flash("Giriş işlemi başarıyla gerçekleşti.", "success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))

            else:
                flash("Parola yanlış!", "danger")
                return redirect(url_for("login"))

        else:
            flash("Kullanici adi bulunamadi", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


# logout


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/addarticle", methods=["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)
    if(request.method == "POST" and form.validate()):
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "insert into articles (TITLE,AUTHOR,CONTENT) values(%s,%s,%s)"
        cursor.execute(sorgu, (title, session["username"], content))
        mysql.connection.commit()
        cursor.close()

        flash("Makale basarili bir sekilde eklendi.", "success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form=form)


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles"
    result = cursor.execute(sorgu)

    if(result > 0):
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")


@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where ID = %s"
    result = cursor.execute(sorgu, (id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")


@app.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from articles where id=%s and AUTHOR = %s"
        result = cursor.execute(sorgu, (id, session["username"]))

        if result == 0:
            flash("Guncelleme islemi yapilamaz")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["TITLE"]
            form.content.data = article["CONTENT"]
            return render_template("update.html", form=form)
    else:
        # POST REQUEST
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu_upd = "update articles set TITLE=%s, CONTENT=%s where ID=%s"
        cursor = mysql.connection.cursor()

        cursor.execute(sorgu_upd, (newTitle, newContent, id))
        mysql.connection.commit()

        flash("Makale basari ile guncellendi", "success")

        return redirect(url_for("dashboard"))


@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where AUTHOR = %s and ID = %s"
    result = cursor.execute(sorgu, (session["username"], id))

    if result > 0:
        sorgu_del = "delete from articles where ID = %s"
        cursor.execute(sorgu_del, (id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("Silme işlemi yapılamadı.")
        return redirect(url_for("index"))


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "select * from articles where TITLE like '%"+keyword+"%' "

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Bulunamadi", "warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles=articles)


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    # sayi = 10
    # sayi_2 = 20
    # return render_template("index.html", number=sayi, number2=sayi_2)
    # article = dict()
    # article["title"] = "Deneme"
    # article["body"] = "Deneme 123"
    # article["author"] = "Tugba"

    return render_template("index.html")


@app.route("/about")
def about():
    return "Hakkimda"


#   __main__ ile terminalden calistirmak istedigimizi belirtiyoruz
if __name__ == "__main__":
    app.run(debug=True)

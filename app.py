from flask import Flask, render_template, make_response
import test
# Create an instance of Flask
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/screen")
def screen():
    df = test.screen()
    resp = make_response(df.to_csv())
    resp.headers["Content-Disposition"] = "attachment; filename=screening.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp
if __name__ == "__main__":
    app.run(debug=True)

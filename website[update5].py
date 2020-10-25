from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename

local_server = True
with open("website_info.json", "r") as c:
    edits = json.load(c)["edits"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=edits["mail_id"],
    MAIL_PASSWORD=edits["mail_pass"]
)
app.config['UPLOAD_FOLDER'] = edits["upload_location"]
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = edits["local_uri"]
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = edits["prod_uri"]

db = SQLAlchemy(app)  # initializing db variable


class Contact(db.Model):
    """slno,name,email,phone,message,date"""
    """ above are names according to sql data base"""
    slno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(12), unique=True)
    message = db.Column(db.String(120), unique=True)
    date = db.Column(db.String(12), unique=True, nullable=True)


class Post(db.Model):
    """slno,title,tagline,content,slug,date"""
    """ above are names according to sql data base"""
    slno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=False, nullable=False)
    tagline = db.Column(db.String(200), unique=False, nullable=True)
    content = db.Column(db.String(500000), unique=True, nullable=False)
    slug = db.Column(db.String(25), unique=True)
    date = db.Column(db.String(12), unique=True, nullable=True)
    img_file = db.Column(db.String(12), unique=True, nullable=True)


@app.route('/', methods=["GET"])
def hello():
    posts = Post.query.filter_by().all()[0:edits['homepage_post_no']]
    return render_template("index.html", edits=edits, posts=posts)


@app.route("/about")
def about():
    return render_template("about.html", edits=edits)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":  # if website requests for posting anything
        # fetching entry from user
        name = request.form.get("name")  # name is a variable in which ("name") from html form is stored
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")
        # adding entry to data base
        entry = Contact(name=name, email=email, phone=phone, message=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        mail.send_message("new message from Blog :" + name,
                          sender=email,
                          recipients=[edits["mail_id"]],
                          body=message + "\n" + phone + "\n" + email
                          )
    return render_template("contact.html", edits=edits)


@app.route('/post', methods=["GET"])
def postpage():
    posts = Post.query.filter_by().all()
    return render_template("postpage.html", edits=edits, posts=posts)


@app.route("/post/<string:post_slug>", methods=["GET", "POST"])
def post(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template("post.html", edits=edits, post=post)


# for login dash-board
@app.route("/dashboard", methods=["GET", "POST"])
def login():
    if ('user' in session and session['user'] == edits['user_name']):
        posts = Post.query.all()
        return render_template("adminpannel.html", edits=edits, posts=posts, post=post)

    if request.method == "POST":
        username = request.form.get("uname")
        userpass = request.form.get("pass")
        if (username == edits['user_name'] and userpass == edits['user_pass']):
            session['user'] = username
            posts = Post.query.all()
            return render_template("adminpannel.html", edits=edits, posts=posts, post=post)
    return render_template("login.html", edits=edits, posts=post)


@app.route("/edit/<string:slno>", methods=["GET", "POST"])
def edit(slno):
    if ('user' in session and session['user'] == edits['user_name']):
        if request.method == "POST":
            title = request.form.get("title")
            tagline = request.form.get("tagline")
            slug = request.form.get("slug")
            content = request.form.get("content")
            img_file = request.form.get("img_file")
            date = datetime.now()

            post = Post.query.filter_by(slno=slno).first()
            post.title = title
            post.tagline = tagline
            post.content = content
            post.slug = slug
            post.img_file = img_file
            post.date = date
            db.session.commit()
            return redirect("/post/" + slug)
        post = Post.query.filter_by(slno=slno).first()
        return render_template("edit.html", edits=edits, post=post,slno=slno)


@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if ('user' in session and session['user'] == edits['user_name']):
        if (request.method == "POST"):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route("/edit/addpost", methods=["GET", "POST"])
def addpost():
    if ('user' in session and session['user'] == edits['user_name']):
        date = datetime.now()
        if request.method == "POST":
            title = request.form.get("title")
            tagline = request.form.get("tagline")
            slug = request.form.get("slug")
            content = request.form.get("content")
            img_file = request.form.get("img_file")

            newpost = Post(title=title, tagline=tagline, content=content, slug=slug, img_file=img_file, date=date)
            db.session.add(newpost)
            db.session.commit()
            return redirect("/post/"+ slug)
        return render_template("addpost.html",post=post,edits=edits)



@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")


@app.route("/delete/<string:slno>", methods=["GET", "POST"])
def delete(slno):
    if ('user' in session and session['user'] == edits['user_name']):
        dlt = Post.query.filter_by(slno=slno).first()
        db.session.delete(dlt)
        db.session.commit()
        return redirect("/dashboard")


if __name__ == '__main__':
    app.run(debug=True)

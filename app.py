from flask import Flask, render_template, request, redirect, flash, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import os, time
from docx2pdf import convert as d2pConverter
from pdf2docx import Converter as p2dConverter
from PyPDF2 import PdfWriter, PdfReader
from werkzeug.utils import secure_filename
import spire.xls as xls
import spire.presentation as ppt


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "docx",
    "doc",
    "xlsx",
    "xls",
    "pptx",
    "ppt",
}

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = (
    "ee64bd532271a9b036fc9f73ee10f1408e4ac27e7b55b5f9d489f88975b35cba"
)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)


# Check for required files extensions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(70), nullable=False)
    is_superuser = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"Contact('{self.email}', '{self.message}')"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    flash('Please log in first')
    return redirect(url_for("login"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sign-up/", methods=["GET", "POST"])
def signUp():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        uname = request.form.get("uname")
        phoneno = request.form.get("phoneno")
        password = request.form.get("password")

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        try:
            new_user = User(
                name=name,
                username=uname,
                email=email,
                phone_number=phoneno,
                password=hashed_password,
            )
            db.session.add(new_user)
            db.session.commit()
            flash("User signed up", "success")
        except:
            flash("Something went wrong", "danger")
        return redirect("/")
    return render_template("sign-up.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect("/")
        else:
            flash("Login unsuccessful. Please check your email and password.", "danger")

    return redirect("/")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect("/")


@app.route("/contact/", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        try:
            new_contact = Contact(name=name, email=email, message=message)
            db.session.add(new_contact)
            db.session.commit()
            print("Contact sent successfully")
            flash("Message Sent Successfully", "success")
        except:
            flash("Something went wrong", "danger")
        return redirect("/contact")
    return render_template("contact_us.html")

@app.route("/view-contact", methods=["GET", "POST"])
@login_required
def show_contact():
    if current_user.is_superuser == True:
        contacts = Contact.query.all()
        return render_template("show-contact.html", contacts=contacts)

@app.route("/pdf-tools/")
@login_required
def pdf_tools():
    return render_template("pdf_tools.html")


@app.route("/uploads/<name>/")
@login_required
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"]+"/out/", name)


@app.route("/pdf-tools/conversions/<conversion>/", methods=["POST", "GET"])
@login_required
def convertor(conversion):
    from_ext, to_ext = conversion.split("-to-")
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        print(file.filename)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename, ext = secure_filename(file.filename).split(".")
            current_time = time.time()
            filename += str(current_time)
            fsaved = os.path.join(
                app.config["UPLOAD_FOLDER"] + "/in/", f"{filename}.{ext}"
            )
            file.save(fsaved)

            if to_ext == "pdf" and from_ext!="pdf":
                match from_ext:
                    case "docx":
                        d2pConverter(
                            os.path.join(
                                app.config["UPLOAD_FOLDER"] + "/in/",
                                f"{filename}.{ext}",
                            ),
                            os.path.join(
                                app.config["UPLOAD_FOLDER"] + "/out/",
                                f"{filename}.{to_ext}",
                            ),
                        )

                    case "xlsx":
                        workbook = xls.Workbook()
                        workbook.LoadFromFile(fsaved)

                        for sheet in workbook.Worksheets:
                            pageSetup = sheet.PageSetup

                            # Set page margins
                            pageSetup.TopMargin = 0.3
                            pageSetup.BottomMargin = 0.3
                            pageSetup.LeftMargin = 0.3
                            pageSetup.RightMargin = 0.3

                        # Set worksheet to fit to page when converting
                        workbook.ConverterSetting.SheetFitToPage = True
                        workbook.SaveToFile(
                            os.path.join(
                                app.config["UPLOAD_FOLDER"] + "/out/",
                                f"{filename}.{to_ext}",
                            ),
                            xls.FileFormat.PDF,
                        )
                        workbook.Dispose()

                    case "pptx":
                        presentation = ppt.Presentation()

                        # Load a PPT or PPTX file
                        presentation.LoadFromFile(fsaved)

                        # Convert the presentation file to PDF and save it
                        presentation.SaveToFile(os.path.join(
                            app.config["UPLOAD_FOLDER"] + "/out/", f"{filename}.{to_ext}"
                        ), ppt.FileFormat.PDF)
                        presentation.Dispose()
                    case _:
                        flash("Not Found", "danger")
                        return redirect(request.url)
                    

            elif from_ext == "pdf" and to_ext != "pdf":
                match to_ext:
                    case "docx":
                        cv = p2dConverter(
                            os.path.join(
                                app.config["UPLOAD_FOLDER"] + "/in/",
                                f"{filename}.{ext}",
                            )
                        )
                        cv.convert(
                            os.path.join(
                                app.config["UPLOAD_FOLDER"] + "/out/",
                                f"{filename}.{to_ext}",
                            ),
                        )

                    case _:
                        flash("Not Found", "danger")
                        return redirect(request.url)
            # return render_template("download.html", filename=f"{filename}.pdf")
            # return render_template("converter.html", filename=f"{filename}.pdf", title="Converte Docx to PDF")
            return redirect(url_for("download_file", name=f"{filename}.{to_ext}"))
        # return redirect(url_for("download_file", name=filename))
    conversion = {
        "conversion": conversion,
        "from_extension": from_ext,
        "to_extension": to_ext
    }
    return render_template("converter.html", filename="", conversion = conversion )

@app.route("/pdf-tools/misc/merge-all/", methods=["POST", "GET"])
@login_required
def merge_all():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        files = request.files.getlist("file")
        current_time = time.time()
        if len(files) == 0:
            flash("No selected file")
            return redirect(request.url)
        merger = PdfWriter()
        for file in files:
            if file and allowed_file(file.filename):
                filename, ext = secure_filename(file.filename).split(".")

                # Check if the file is pdf or not
                if ext != "pdf":
                    flash("Files are not pdfs!", "danger")
                    return redirect(request.url)

                filename += str(current_time)
                file.save(
                    os.path.join(app.config["UPLOAD_FOLDER"] + "/in/", f"{filename}.{ext}")
                )
                merger.append(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"] + "/in/", f"{filename}.{ext}"
                    )
                )
        outfile = os.path.join(app.config["UPLOAD_FOLDER"] + "/out/", f"{filename}.pdf")
        merger.write(outfile)
        return redirect(url_for("download_file", name=f"{filename}.pdf"))
    return render_template("merge_all.html")


@app.route("/pdf-tools/misc/lossless-compress/", methods=["GET", "POST"])
@login_required
def misc_lossless_compress():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        print(file.filename)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename, ext = secure_filename(file.filename).split(".")
            current_time = time.time()
            filename += str(current_time)
            fsaved = os.path.join(
                app.config["UPLOAD_FOLDER"] + "/in/", f"{filename}.{ext}"
            )
            fupload = os.path.join(app.config["UPLOAD_FOLDER"] + "/out/", f"{filename}.{ext}")

            reader = PdfReader(fsaved)
            writer = PdfWriter()

            for page in reader.pages:
                page.compress_content_streams()  # This is CPU intensive!
                writer.add_page(page)

            with open(fupload, "wb") as f:
                writer.write(f)
            return redirect(url_for("download_file", name=f"{filename}.{ext}"))
    return render_template("misc_lossless_compress.html")


@app.route("/pdf-tools/misc/split/", methods=["GET", "POST"])
@login_required
def split():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        print(file.filename)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename, ext = secure_filename(file.filename).split(".")
            current_time = time.time()
            filename += str(current_time)
            fsaved = os.path.join(
                app.config["UPLOAD_FOLDER"] + "/in/", f"{filename}.{ext}"
            )
            fupload = os.path.join(
                app.config["UPLOAD_FOLDER"] + "/out/", f"{filename}.{ext}"
            )




if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)

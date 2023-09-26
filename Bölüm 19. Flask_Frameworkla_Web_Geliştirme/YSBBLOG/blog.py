from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators, EmailField
from wtforms.validators import InputRequired, Email
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı Giriş Dacorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Bu sayfayı görüntülemek için lütfen giriş yapın...', 'danger')
            return redirect(url_for('login'))
    return decorated_function


#Kullanıcı kayıt formu
class RegistrationForm(Form):
    name = StringField('İsim Soyisim', validators=[validators.Length(min=4,max=25)])
    username = StringField('Kullanıcı Adı', validators=[validators.Length(min=5,max=35)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('Parola:', validators=[
        validators.DataRequired(message='Lütfen Parola Belirleyin'),
        validators.EqualTo(fieldname='confirm',message='Parolanız Uyuşmuyor...')
    ])
    confirm = PasswordField('Parola Doğrula')

class LoginForm(Form):
    username = StringField('Kullanıcı Adı')
    password= PasswordField('Parola')

app = Flask(__name__)
app.secret_key='ysbblog'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ysbblog'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html',)
@app.route('/about')
def about():
    return render_template('about.html')

#Makale Sayfası
@app.route('/articles')
def articles():
    cursor = mysql.connection.cursor()

    sorgu = 'SELECT * FROM articles'

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template('articles.html',articles=articles)
    else:
        return render_template('articles.html')

# @app.route('/article/<string:id>') #dinamik id
#def detail(id):
#    return 'Article Id:' + id 

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = 'SELECT * FROM articles where author = %s'

    result = cursor.execute(sorgu,(session['username'],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template('dashboard.html',articles=articles)
    else:
        return render_template('dashboard.html')

#Kayıt olma
@app.route('/register',methods=['GET','POST'])
def register():
    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate(): #form.validate() ile formları denetlemeyi sağladık
        name = form.name.data           #formdaki bilgileri aldık ve name'a eşitledik
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) #password'u şifrledik

        cursor = mysql.connection.cursor() #phpmyadmin üzerinde işlem yapmak cursor'u oluşturduk

        sorgu = 'INSERT into users(name,username,email,password) VALUES(%s,%s,%s,%s)' #name,user,..,..  %s'lerin yerine geçecek

        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit() #veri tabanında güncelleme yaptığımız için commit yapılması gerekiyor.

        cursor.close() #cursor'ı kapatarak boşa çalışmasından kaçınıyoruz
        flash('Başarıyla Kayıt Oldunuz...',category='success')
        return redirect(url_for('login'))
    else:
        return render_template('register.html',form=form)

#Login İşlemi
@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm(request.form)
    if request.method == 'POST':
        username=form.username.data
        password_entered=form.password.data

        cursor = mysql.connection.cursor()

        sorgu = 'SELECT * FROM users where username = %s'
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data['password']
            if sha256_crypt.verify(password_entered,real_password):
                flash('Başarıyla Giriş Yaptınız...','success')

                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('index'))
            else:
                flash('Parolanızı Yanlış Girdiniz...','danger')
                return redirect(url_for('login'))
        else:
            flash('Kullanıcı Adı Bulunamadı...','danger') #dangerla bağladık
            return redirect(url_for('login')) #tekrar login ekranına döndük

    return render_template('login.html',form=form)

#Detay Sayfası
@app.route('/article/<string:id>') #dinamik id
def article(id): #dinamik url'den dolayı id geliyor
    cursor = mysql.connection.cursor()

    sorgu = 'SELECT * FROM articles where id = %s'
    result = cursor.execute(sorgu,(id),)
    if result > 0:
        article = cursor.fetchone()
        return render_template('article.html',article=article)
    else:
        return render_template('article.html')


#Logout işlemi
@app.route('/logout')
def logout():
    session.clear() #session'ı sonlandıracak
    return redirect(url_for('index'))

#Makale Ekleme
@app.route('/addarticle', methods = ['GET','POST'])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        content = form.content.data
        
        cursor = mysql.connection.cursor()

        sorgu ='Insert into articles(title,author,content) VALUES(%s,%s,%s)'

        cursor.execute(sorgu,(title,session['username'],content))

        mysql.connection.commit()

        cursor.close()

        flash('Makale Başarıyla Eklendi','success')

        return redirect(url_for('dashboard'))

    return render_template('addarticle.html',form=form)

#Makale Silme
@app.route('/delete/<string:id>') #dinamik id
@login_required
def delete(id): #dinamik url'den dolayı id geliyor
    cursor = mysql.connection.cursor()

    sorgu = 'SELECT * FROM articles WHERE author = %s and id = %s'

    result= cursor.execute(sorgu,(session['username'],id))

    if result>0:
        sorgu2 = 'DELETE from articles WHERE id = %s'
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for('dashboard'))
    else:
        flash('Bu makaleyi silme yetkiniz yok veya böyle bir makale yok','danger')
        return redirect(url_for('index'))

#Makale Güncelleme
@app.route('/edit/<string:id>',methods =['GET','POST'])
@login_required
def update(id): #dinamik url'den dolayı id geliyor
    if request.method == 'GET': #get mi post mu kontrolünü yapacağız
        cursor = mysql.connection.cursor()

        sorgu = 'SELECT * FROM articles WHERE author = %s and id = %s'
        result= cursor.execute(sorgu,(session['username'],id))

        if result==0:
            flash('Böyle bir makale yok veya işleme yetkiniz yok','danger')
            return redirect(url_for('index'))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article['title']
            form.content.data = article['content']
            return render_template('update.html',form=form)

    else: #POST REQUEST
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = 'UPDATE articles SET title = %s, content=%s WHERE id = %s'

        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash('Makale Başarıyla Güncellendir','success')
        return redirect(url_for('dashboard'))

#Makele Form
class ArticleForm(Form):
    title = StringField('Makale Başlığı',validators=[validators.length(min=5,max=100)])
    content = TextAreaField('Makale İçeriği',validators=[validators.length(min=10)]) #Uzun bir yazı olacağından textareafield

#Arama URL
@app.route('/search', methods = ['GET','POST']) #sadece post requestte çalışması lazım. 
def search():
    if request.method == 'GET':
        return redirect(url_for('index'))
    else:
        keyword = request.form.get('keyword')

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM articles WHERE title like '%" + keyword +"%'"

        result =cursor.execute(sorgu)

        if result==0:
            flash('Aranan Kelimeye Uygun Makale Bulunamadı','warning')
            return redirect(url_for('articles'))
        else:
            articles=cursor.fetchall()

            return render_template('articles.html',articles=articles)

if __name__ == '__main__':
    app.run(debug=True)
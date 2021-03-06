# Importation
from flask import Flask
from flask import render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import numpy as np
import pandas as pd 
import pickle
from sklearn.feature_extraction.text import CountVectorizer


app = Flask(__name__)

model = pickle.load(open('model.pkl', 'rb'))


# Clé de sécurtié 
app.secret_key = 'your secret key'

# Détails de database 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'wiem123'
app.config['MYSQL_DB'] = 'projet'

# Intialisation MySQL
mysql = MySQL(app)


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/connexion', methods=['GET', 'POST'])
def login():
       # Message de sortie en cas d'error
    msg = ''
    # Vérifier si "username" and "password" POST requests exist 
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Création des variables username et password (valeur saisie dans le formulaire)
        username = request.form['username']
        password = request.form['password']
        # vérifer si le compte existe
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        # Fetch
        account = cursor.fetchone()
        # si le compte existe dans notre table users
        if account:
            # Création d'une session 
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # si le compte n'existe pas affichage d'un message: username/password incorrect
            msg = 'Incorrect username/password!'

    return render_template('login.html', msg=msg)



@app.route('/logout')
def logout():
    # données de session
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return render_template('login.html')


@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
  
    msg = ''
    # vérification si nom d'utilisateur/motde passe et email existe
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:

        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        msg=username
         # Vérifier si utilisateur et email existe
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND email = %s', (username, email))
        account = cursor.fetchone()
        # Si le compte existe déjà
        if account:
            msg = 'Le compte existe déjà'
            return render_template('inscription.html', msg=msg)

        # Si le compte n'existe pas
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s)',(username, password, email))
            mysql.connection.commit()
            msg = 'Votre compte a bien été créé'

    return render_template('inscription.html', msg=msg)



@app.route('/home')
def home():
    # vérifier si l'utilisateur est connecté
    if 'loggedin' in session:
        # Si l'utilisateur est connecté --> home.html
        return render_template('home.html', username=session['username'])
    # Si l'utilisateur est déconnecte --> login.html
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    # vérifier si l'utilisateur est connecté
    if 'loggedin' in session:
        # Récuperation des informations de l'utilisateur connecté
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Afficher la page profile avec les informations de l'utilisateur
        return render_template('profile.html', account=account)

    return redirect(url_for('login'))


@app.route('/score')
def score():
	return render_template('score.html')

@app.route('/predict',methods=['POST'])
def predict():
    int_features = [int(x) for x in request.form.values()]
    final_features = [np.array(int_features)]
    prediction = model.predict(final_features)
    output = round(prediction[0], 2)
    return render_template('score.html', prediction_text='Votre salaire va être vers {} DT'.format(output))


@app.route('/send_email')
def send():
	return render_template('email.html')


@app.route('/predict_spam',methods=['POST'])
def spam():
    df= pd.read_csv("spam.csv", encoding="latin-1")
    df.drop(['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4'], axis=1, inplace=True)
    # Features and Labels
    df['label'] = df.label.map({'ham': 0, 'spam': 1})
    X = df['message']
    y = df['label']
    
    # Extraction des features avec CountVectorizer
    cv = CountVectorizer()
    X = cv.fit_transform(X) # Fit the Data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
    #Naive Bayes Classifier
    from sklearn.naive_bayes import MultinomialNB

    clf = MultinomialNB()
    clf.fit(X_train,y_train)
    clf.score(X_test,y_test)

    if request.method == 'POST':
        message = request.form['message']
        data = [message]
        vect = cv.transform(data).toarray()
        my_prediction = clf.predict(vect)
    return render_template('email.html',prediction = my_prediction)
    

    
if __name__ == '__main__':
    app.run(debug=True)

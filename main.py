import os
from datetime import datetime, time
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gestion_lab'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def get_tp_status(start_time, end_time):
    now = datetime.now().time()
    if now < start_time:
        return 'En attente'
    elif start_time <= now <= end_time:
        return 'En cours'
    else:
        return 'Terminé'

@app.route('/')
def index():
    try:
        cur = mysql.connection.cursor()
        
        # Récupération des TP du jour
        today = datetime.now().date()
        cur.execute("""
            SELECT 
                tp.id_tp,
                tp.nom_tp,
                tp.heure_debut,
                tp.heure_fin,
                CONCAT(p.prenom, ' ', p.nom) AS professeur,
                m.nom_matiere AS matiere,
                l.nom_laboratoire
            FROM tp
            JOIN professeur p ON tp.id_prof = p.id_prof
            JOIN matiere m ON tp.id_matiere = m.id_matiere
            JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
            WHERE DATE(tp.heure_debut) = %s
            ORDER BY tp.heure_debut
        """, (today,))
        
        tps_jour = []
        for tp in cur.fetchall():
            start = tp['heure_debut'].time()
            end = tp['heure_fin'].time()
            
            tps_jour.append({
                **tp,
                'statut': get_tp_status(start, end),
                'heure_debut': tp['heure_debut'].strftime('%H:%M'),
                'heure_fin': tp['heure_fin'].strftime('%H:%M')
            })

        # Alertes stock (seuil fixe à 10)
        cur.execute("""
            SELECT 
                a.nom_article,
                a.unite_mesure,
                sm.quantite
            FROM article a
            JOIN stock_magasin sm ON a.id_stock_magasin = sm.id_stock_magasin
            WHERE sm.quantite < 10
        """)
        alertes_stock = cur.fetchall()

    except Exception as e:
        flash(f"Erreur base de données: {str(e)}", "danger")
        tps_jour = []
        alertes_stock = []
    finally:
        cur.close()
    
    return render_template('index.html',
                         tps_jour=tps_jour,
                         alertes_stock=alertes_stock,
                         date_actuelle=datetime.now().strftime('%d/%m/%Y'))

@app.route('/creer_tp', methods=['GET', 'POST'])
def creer_tp():
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("SELECT id_prof, prenom, nom FROM professeur")
        professeurs = cur.fetchall()
        
        cur.execute("SELECT id_matiere, nom_matiere FROM matiere")
        matieres = cur.fetchall()
        
        cur.execute("SELECT id_laboratoire, nom_laboratoire FROM laboratoire")
        laboratoires = cur.fetchall()

        if request.method == 'POST':
            nom_tp = request.form['nom_tp']
            id_prof = request.form['id_prof']
            id_matiere = request.form['id_matiere']
            id_laboratoire = request.form['id_laboratoire']
            date_tp = request.form['date_tp']
            heure_debut = f"{date_tp} {request.form['heure_debut']}"
            heure_fin = f"{date_tp} {request.form['heure_fin']}"
            annee_scolaire = request.form['annee_scolaire']

            cur.execute("""
                INSERT INTO tp (
                    nom_tp, 
                    heure_debut, 
                    heure_fin, 
                    annee_scolaire, 
                    id_laboratoire, 
                    id_matiere, 
                    id_prof
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                nom_tp, 
                heure_debut, 
                heure_fin, 
                annee_scolaire, 
                id_laboratoire, 
                id_matiere, 
                id_prof
            ))
            
            mysql.connection.commit()
            flash("TP créé avec succès!", "success")
            return redirect(url_for('index'))

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)}", "danger")
    finally:
        cur.close()

    return render_template('creer_tp.html',
                         professeurs=professeurs,
                         matieres=matieres,
                         laboratoires=laboratoires)

@app.route('/ajouter_professeur', methods=['GET', 'POST'])
def ajouter_professeur():
    if request.method == 'POST':
        prenom = request.form['prenom']
        nom = request.form['nom']
        email = request.form['email']
        telephone = request.form['telephone']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO professeur (prenom, nom, email, telephone)
                VALUES (%s, %s, %s, %s)
            """, (prenom, nom, email, telephone))
            mysql.connection.commit()
            flash("Professeur ajouté avec succès!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur: {str(e)}", "danger")
        finally:
            cur.close()
    
    return render_template('ajouter_professeur.html')

@app.route('/ajouter_matiere', methods=['GET', 'POST'])
def ajouter_matiere():
    if request.method == 'POST':
        nom_matiere = request.form['nom_matiere']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO matiere (nom_matiere)
                VALUES (%s)
            """, (nom_matiere,))
            mysql.connection.commit()
            flash("Matière ajoutée avec succès!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur: {str(e)}", "danger")
        finally:
            cur.close()
    
    return render_template('ajouter_matiere.html')

if __name__ == '__main__':
    app.run(debug=True)
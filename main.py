import os
from datetime import datetime, time
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration de la base de données
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
                TIME(tp.heure_debut) AS heure_debut,
                TIME(tp.heure_fin) AS heure_fin,
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
            start = datetime.strptime(tp['heure_debut'], '%H:%M:%S').time()
            end = datetime.strptime(tp['heure_fin'], '%H:%M:%S').time()
            
            tps_jour.append({
                **tp,
                'statut': get_tp_status(start, end),
                'heure_debut': start.strftime('%H:%M'),
                'heure_fin': end.strftime('%H:%M')
            })

        # Récupération des alertes stock
        cur.execute("""
            SELECT 
                a.nom_article,
                a.unite_mesure,
                sm.quantite,
                t.seuil_urgence
            FROM article a
            JOIN stock_magasin sm ON a.id_stock_magasin = sm.id_stock_magasin
            JOIN type t ON a.id_type = t.id_type
            WHERE sm.quantite <= t.seuil_urgence
            ORDER BY sm.quantite ASC
            LIMIT 5
        """)
        alertes_stock = cur.fetchall()

    except Exception as e:
        flash(f"Erreur de base de données : {str(e)}", "danger")
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
    if request.method == 'POST':
        try:
            nom_tp = request.form['nom_tp']
            id_prof = request.form['id_prof']
            id_matiere = request.form['id_matiere']
            id_laboratoire = request.form['id_laboratoire']
            heure_debut = request.form['heure_debut']
            heure_fin = request.form['heure_fin']

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO tp (nom_tp, id_prof, id_matiere, id_laboratoire, heure_debut, heure_fin)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nom_tp, id_prof, id_matiere, id_laboratoire, heure_debut, heure_fin))
            mysql.connection.commit()
            
            flash("TP créé avec succès", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Erreur lors de la création du TP : {str(e)}", "danger")
        finally:
            cur.close()

    return render_template('creer_tp.html')



if __name__ == '__main__':
    app.run(debug=True)
import os
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from dateutil.relativedelta import relativedelta
from flask_session import Session 
from flask_wtf.csrf import CSRFProtect
import mysql.connector as pymysql
import mysql.connector
from mysql.connector import Error



app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = os.environ.get('SECRET_KEY') or 'une_phrase_secrete_complexe_ici'  # Ex: 'azerty1234!@#$567890' 
# Configuration de session (ajoutez ceci après app.secret_key)
app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR='/tmp/flask_sessions',  # Créez ce dossier
    SESSION_COOKIE_NAME='lab_session',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,  # True en production
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)
Session(app)
# Configuration MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gestion_lab'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)  # <-- Déplacer cette ligne ICI



def get_tp_status(start_time, end_time):
    now = datetime.now().time()
    if now < start_time:
        return 'En attente'
    elif start_time <= now <= end_time:
        return 'En cours'
    else:
        return 'Terminé'



# Créer les utilisateurs au démarrage
def create_default_users():
    with app.app_context():
        cur = mysql.connection.cursor()
        try:
            # Vérifier si la table existe
            cur.execute("SHOW TABLES LIKE 'utilisateur'")
            if not cur.fetchone():
                cur.execute("""
                    CREATE TABLE utilisateur (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        role ENUM('admin', 'user') NOT NULL DEFAULT 'user'
                    )
                """)
                print("Table utilisateur créée")

            # Créer admin
            cur.execute("SELECT * FROM utilisateur WHERE username = 'admin'")
            if not cur.fetchone():
                hashed_pw = generate_password_hash('admin123')
                cur.execute("INSERT INTO utilisateur (username, password, role) VALUES (%s, %s, 'admin')",
                          ('admin', hashed_pw))
                print("Admin créé")

            # Créer user
            cur.execute("SELECT * FROM utilisateur WHERE username = 'user'")
            if not cur.fetchone():
                hashed_pw = generate_password_hash('user123')
                cur.execute("INSERT INTO utilisateur (username, password) VALUES (%s, %s)",
                          ('user', hashed_pw))
                print("User créé")

            mysql.connection.commit()
        except Exception as e:
            print(f"ERREUR CRITIQUE : {str(e)}")
            raise  # Propager l'erreur pour la voir dans les logs
        finally:
            cur.close()

# Supprimez la première définition de create_default_users() (lignes 42 à 60)
# Gardez seulement la deuxième définition (à partir de la ligne 62)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM utilisateur WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
            
            if user:
                print(f"Utilisateur trouvé : {user['username']}")
                if check_password_hash(user['password'], password):
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['show_welcome'] = True
                    session.modified = True
                    return redirect(url_for('index'))
                else:
                    flash('Mot de passe incorrect', 'danger')
            else:
                flash('Utilisateur inconnu', 'danger')
            
            return redirect(url_for('login'))
        
        except Exception as e:
            print(f"Erreur de connexion : {str(e)}")
            flash('Erreur système', 'danger')
    
    return render_template('login.html')
@app.before_request
def verify_access():
    # Liste de toutes les routes protégées
    protected_routes = [
        'index', 'liste_professeurs', 'creer_tp', 'editer_tp', 
        'supprimer_tp', 'creer_recu', 'liste_matieres', 'creer_matiere',
        'editer_matiere', 'supprimer_matiere', 'liste_laboratoires',
        'creer_laboratoire', 'editer_laboratoire', 'supprimer_laboratoire'
    ]
    
    if request.endpoint in protected_routes and not session.get('user_id'):
        return redirect(url_for('login'))
    
    # Vérification droits admin
    admin_only_routes = [
        'creer_professeur', 'supprimer_professeur',
        'creer_matiere', 'supprimer_matiere',
        'creer_laboratoire', 'supprimer_laboratoire'
    ]
    
    if request.endpoint in admin_only_routes and session.get('role') != 'admin':
        abort(403, description="Accès réservé aux administrateurs")
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))
@app.before_request
def verify_access():
    excluded = ['login', 'static', 'logout']
    
    if request.endpoint in excluded:
        return
    
    # Debug session
    print(f"Session vérifiée: {dict(session)}")
    
    if 'user_id' not in session:
        print("Redirection vers login - Session invalide")
        return redirect(url_for('login'))
    
    # Garder la session active
    session.permanent = True
    session.modified = True

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html', description=e.description), 403

@app.route('/')
def index():

    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    show_welcome = session.pop('show_welcome', False)  # <-- Récupérer et supprimer le flag

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
            LEFT JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
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

        # Alertes stock
        cur.execute("""
            SELECT 
                a.nom_article,
                a.unite_mesure,
                sm.quantite
            FROM stock_magasin sm
            JOIN article a ON sm.id_stock_magasin = a.id_stock_magasin
            WHERE sm.quantite < 10
        """)
        alertes_stock = cur.fetchall()

        # Statistiques
        cur.execute("SELECT COUNT(*) AS total FROM professeur")
        stats_prof = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) AS total FROM matiere")
        stats_mat = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) AS total FROM laboratoire")
        stats_lab = cur.fetchone()['total']

    except Exception as e:
        flash(f"Erreur base de données: {str(e)}", "danger")
        tps_jour = []
        alertes_stock = []
        stats_prof = stats_mat = stats_lab = 0
    finally:
        cur.close()
    
    return render_template('index.html',
                            show_welcome=show_welcome,
                         tps_jour=tps_jour,
                         alertes_stock=alertes_stock,
                         stats={
                             'professeurs': stats_prof,
                             'matieres': stats_mat,
                             'laboratoires': stats_lab
                         },
                         date_actuelle=datetime.now().strftime('%d/%m/%Y'))

@app.route('/supprimer_tp/<int:id>', methods=['POST'])
def supprimer_tp(id):
    redirect_week = request.args.get('redirect_week', 0, type=int)
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM tp WHERE id_tp = %s", (id,))
        mysql.connection.commit()
        flash("TP supprimé avec succès", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)}", "danger")
    finally:
        cur.close()
    
    return redirect(url_for('emploi', week_offset=redirect_week))

CRENEAUX = {
        'P1': ('08:00', '09:30'),
        'P2': ('09:45', '11:15'),
        'P3': ('11:30', '13:00'),
        'P4': ('15:10', '16:40'),
        'P5': ('17:00', '18:30')
    }
@app.route('/creer_tp', methods=['GET', 'POST'])
def creer_tp():
    CRENEAUX = {
        'P1': ('08:00', '09:30'),
        'P2': ('09:45', '11:15'),
        'P3': ('11:30', '13:00'),
        'P4': ('15:10', '16:40'),
        'P5': ('17:00', '18:30')
    }

    from_emploi = 'date' in request.args
    default_date = request.args.get('date')
    default_periode = request.args.get('periode', None)

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_prof, prenom, nom FROM professeur")
    professeurs = cur.fetchall()
    cur.execute("SELECT id_matiere, nom_matiere FROM matiere")
    matieres = cur.fetchall()
    cur.execute("SELECT id_laboratoire, nom_laboratoire FROM laboratoire")
    laboratoires = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        try:
            data = {
                'nom_tp': request.form['nom_tp'].strip(),
                'id_prof': request.form.get('id_prof', '').strip(),
                'id_matiere': request.form.get('id_matiere', '').strip(),
                'id_laboratoire': request.form.get('id_laboratoire', '').strip(),
                'date_tp': request.form['date_tp'].strip(),
                'periodes': request.form.getlist('periodes'),
                'annee_scolaire': request.form['annee_scolaire'].strip()
            }

            if from_emploi and not data['date_tp']:
                data['date_tp'] = default_date

            if not all([data['nom_tp'], data['id_prof'], data['id_matiere'], data['date_tp']]):
                flash("Tous les champs obligatoires (*) doivent être remplis", "danger")
                return render_template('creer_tp.html',
                                    professeurs=professeurs,
                                    matieres=matieres,
                                    CRENEAUX=CRENEAUX,
                                    laboratoires=laboratoires,
                                    from_emploi=from_emploi,
                                    default_date=default_date)

            if not data['periodes']:
                flash("Veuillez sélectionner au moins un créneau horaire", "danger")
                return render_template('creer_tp.html',
                                    professeurs=professeurs,
                                    matieres=matieres,
                                    CRENEAUX=CRENEAUX,
                                    laboratoires=laboratoires,
                                    from_emploi=from_emploi,
                                    default_date=default_date)

            cur = mysql.connection.cursor()
            created_count = 0
            
            for periode in data['periodes']:
                if periode in CRENEAUX:
                    debut, fin = CRENEAUX[periode]
                    heure_debut = datetime.strptime(f"{data['date_tp']} {debut}", "%Y-%m-%d %H:%M")
                    heure_fin = datetime.strptime(f"{data['date_tp']} {fin}", "%Y-%m-%d %H:%M")

                    # Remplacer la requête SQL existante par :
                    cur.execute("""
                        SELECT id_tp 
                        FROM tp 
                        WHERE (
                            (heure_debut < %s AND heure_fin > %s) OR
                            (heure_debut < %s AND heure_fin > %s) OR
                            (heure_debut BETWEEN %s AND %s) OR
                            (heure_fin BETWEEN %s AND %s)
                        )
                        AND id_prof = %s
                    """, (
                        heure_fin, heure_debut,
                        heure_debut, heure_fin,
                        heure_debut, heure_fin,
                        heure_debut, heure_fin,
                        data['id_prof']
                    ))
                    if cur.fetchone():
                        flash(f"Le créneau {periode} ({debut}-{fin}) est déjà occupé !", "danger")
                        mysql.connection.rollback()
                        return render_template('creer_tp.html',
                                            professeurs=professeurs,
                                            matieres=matieres,
                                            CRENEAUX=CRENEAUX,
                                            laboratoires=laboratoires,
                                            from_emploi=from_emploi,
                                            default_date=default_date)

                    cur.execute("""
                        INSERT INTO tp (
                            nom_tp, heure_debut, heure_fin, annee_scolaire,
                            id_laboratoire, id_matiere, id_prof
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data['nom_tp'], heure_debut, heure_fin, data['annee_scolaire'],
                        data['id_laboratoire'], data['id_matiere'], data['id_prof']
                    ))
                    created_count += 1

            mysql.connection.commit()
            flash(f"{created_count} TP créés avec succès!", "success")
            return redirect(url_for('emploi' if from_emploi else 'index'))

        except ValueError as e:
            flash(f"Format de date invalide : {str(e)}", "danger")
            return render_template('creer_tp.html',
                                professeurs=professeurs,
                                matieres=matieres,
                                CRENEAUX=CRENEAUX,
                                laboratoires=laboratoires,
                                from_emploi=from_emploi,
                                default_date=default_date)
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur MySQL: {str(e)}", "danger")
            return render_template('creer_tp.html',
                                professeurs=professeurs,
                                matieres=matieres,
                                CRENEAUX=CRENEAUX,
                                laboratoires=laboratoires,
                                from_emploi=from_emploi,
                                default_date=default_date)

    return render_template('creer_tp.html',
                         professeurs=professeurs,
                         matieres=matieres,
                         laboratoires=laboratoires,
                         CRENEAUX=CRENEAUX,
                         default_date=default_date,
                         default_periodes=[default_periode] if default_periode else [],
                         from_emploi=from_emploi)

@app.route('/editer_tp/<int:id>', methods=['GET', 'POST'])
def editer_tp(id):
    CRENEAUX = {
        'P1': ('08:00', '09:30'),
        'P2': ('09:45', '11:15'),
        'P3': ('11:30', '13:00'),
        'P4': ('15:10', '16:40'),
        'P5': ('17:00', '18:30')
    }

    redirect_week = request.args.get('redirect_week', 0, type=int)
    from_emploi = 'redirect_week' in request.args
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT 
                tp.*,
                DATE(tp.heure_debut) AS date_tp,
                TIME(tp.heure_debut) AS heure_debut_time,
                TIME(tp.heure_fin) AS heure_fin_time,
                p.prenom,
                p.nom,
                m.nom_matiere,
                l.nom_laboratoire
            FROM tp
            JOIN professeur p ON tp.id_prof = p.id_prof
            JOIN matiere m ON tp.id_matiere = m.id_matiere
            LEFT JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
            WHERE tp.id_tp = %s
        """, (id,))
        tp = cur.fetchone()

        if not tp:
            flash("TP introuvable", "danger")
            return redirect(url_for('emploi', week_offset=redirect_week))

        if request.method == 'POST':
            data = {
                'nom_tp': request.form['nom_tp'].strip(),
                'id_prof': request.form['id_prof'].strip(),
                'id_matiere': request.form['id_matiere'].strip(),
                'id_laboratoire': request.form.get('id_laboratoire', '').strip() or None,
                'date_tp': request.form['date_tp'].strip(),
                'periodes': request.form.getlist('periodes'),
                'annee_scolaire': request.form['annee_scolaire'].strip(),
                'redirect_week': request.form.get('redirect_week', 0, type=int)
            }

            if from_emploi and not data['date_tp']:
                data['date_tp'] = tp['date_tp'].strftime('%Y-%m-%d')

            if not all([data['nom_tp'], data['id_prof'], data['id_matiere'], data['date_tp']]):
                flash("Tous les champs obligatoires doivent être remplis", "danger")
                return render_edit_form(cur, tp, data, redirect_week, from_emploi)

            if not data['periodes']:
                flash("Veuillez sélectionner au moins un créneau horaire", "danger")
                return render_edit_form(cur, tp, data, redirect_week, from_emploi)

            try:
                # Suppression ancien TP
                cur.execute("DELETE FROM tp WHERE id_tp = %s", (id,))
                
                # Vérification et création des nouveaux TP
                created_count = 0
                for periode in data['periodes']:
                    if periode in CRENEAUX:
                        debut, fin = CRENEAUX[periode]
                        heure_debut = datetime.strptime(f"{data['date_tp']} {debut}", "%Y-%m-%d %H:%M")
                        heure_fin = datetime.strptime(f"{data['date_tp']} {fin}", "%Y-%m-%d %H:%M")

                        cur.execute("""
                                SELECT id_tp 
                                FROM tp 
                                WHERE (
                                    (heure_debut < %s AND heure_fin > %s) OR
                                    (heure_debut < %s AND heure_fin > %s) OR
                                    (heure_debut BETWEEN %s AND %s) OR
                                    (heure_fin BETWEEN %s AND %s)
                                )
                                AND id_prof = %s
                                AND id_tp != %s  <!-- Exclusion du TP actuel -->
                            """, (
                                heure_fin, heure_debut,
                                heure_debut, heure_fin,
                                heure_debut, heure_fin,
                                heure_debut, heure_fin,
                                data['id_prof'], id
                            ))
                        if cur.fetchone():
                            flash(f"Le créneau {periode} ({debut}-{fin}) est déjà occupé !", "danger")
                            mysql.connection.rollback()
                            return render_edit_form(cur, tp, data, redirect_week, from_emploi)

                        cur.execute("""
                            INSERT INTO tp (
                                nom_tp, heure_debut, heure_fin, annee_scolaire,
                                id_laboratoire, id_matiere, id_prof
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            data['nom_tp'], heure_debut, heure_fin, data['annee_scolaire'],
                            data['id_laboratoire'], data['id_matiere'], data['id_prof']
                        ))
                        created_count += 1

                mysql.connection.commit()
                flash(f"{created_count} TP modifiés avec succès!", "success")
                return redirect(url_for('emploi', week_offset=data['redirect_week']) if from_emploi else url_for('index'))

            except ValueError as e:
                flash(f"Erreur de format : {str(e)}", "danger")
                return render_edit_form(cur, tp, data, redirect_week, from_emploi)
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur base de données : {str(e)}", "danger")
                return render_edit_form(cur, tp, data, redirect_week, from_emploi)

        return render_edit_form(cur, tp, None, redirect_week, from_emploi)

    except Exception as e:
        flash(f"Erreur système : {str(e)}", "danger")
        return redirect(url_for('emploi', week_offset=redirect_week))
    finally:
        cur.close()

def render_edit_form(cur, tp, form_data, redirect_week, from_emploi):
    """Factorise le rendu du formulaire d'édition"""
    # Conversion des timedelta en time
    debut_time = convert_timedelta(tp['heure_debut_time'])
    fin_time = convert_timedelta(tp['heure_fin_time'])
    
    # Détermination des créneaux sélectionnés
    periodes_selectionnes = []
    for periode, (debut, fin) in CRENEAUX.items():
        debut_periode = datetime.strptime(debut, "%H:%M").time()
        fin_periode = datetime.strptime(fin, "%H:%M").time()
        
        if debut_periode <= debut_time and fin_periode >= fin_time:
            periodes_selectionnes.append(periode)

    # Récupération des données pour les listes déroulantes
    cur.execute("SELECT id_prof, prenom, nom FROM professeur")
    professeurs = cur.fetchall()
    cur.execute("SELECT id_matiere, nom_matiere FROM matiere")
    matieres = cur.fetchall()
    cur.execute("SELECT id_laboratoire, nom_laboratoire FROM laboratoire")
    laboratoires = cur.fetchall()

    return render_template('editer_tp.html',
                        tp=tp,
                        CRENEAUX=CRENEAUX,
                        periodes_selectionnes=periodes_selectionnes,
                        professeurs=professeurs,
                        matieres=matieres,
                        laboratoires=laboratoires,
                        redirect_week=redirect_week,
                        from_emploi=from_emploi)

def convert_timedelta(td):
    """Convertit un timedelta SQL en objet datetime.time"""
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    return time(hour=hours, minute=minutes)

@app.route('/creer_recu/<int:id_tp>', methods=['GET', 'POST'])
def creer_recu(id_tp):
    cur = mysql.connection.cursor()
    try:
        # Récupérer les informations du TP
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
            LEFT JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
            WHERE tp.id_tp = %s
        """, (id_tp,))
        
        tp_data = cur.fetchone()
        if not tp_data:
            flash("TP introuvable", "danger")
            return redirect(url_for('index'))

        # Récupérer les articles utilisés
        cur.execute("""
            SELECT 
                a.nom_article,
                a.unite_mesure,
                h.quantite,
                h.degradation,
                h.date_utilisation
            FROM historique_ h
            JOIN article a ON h.id_article = a.id_article
            WHERE h.id_tp = %s
        """, (id_tp,))
        articles = cur.fetchall()

        if request.method == 'POST':
            # Enregistrer le reçu dans la base
            try:
                # Insertion du reçu principal
                cur.execute("""
                    INSERT INTO recu (id_tp, id_prof, date_emission, degradation, observations)
                    VALUES (%s, %s, NOW(), %s, %s)
                """, (
                    id_tp,
                    tp_data['id_prof'],
                    request.form.get('degradation', 0),
                    request.form.get('observations', '')
                ))
                recu_id = cur.lastrowid

                # Insertion des lignes du reçu
                for article in articles:
                    cur.execute("""
                        INSERT INTO ligne_recu (id_article, id_recu, quantite)
                        VALUES (%s, %s, %s)
                    """, (
                        article['id_article'],
                        recu_id,
                        article['quantite']
                    ))

                mysql.connection.commit()
                flash("Reçu généré avec succès", "success")
                return redirect(url_for('index'))

            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur lors de la création du reçu : {str(e)}", "danger")

        return render_template('creer_recu.html',
                             tp=tp_data,
                             articles=articles,
                             maintenant=datetime.now())

    except Exception as e:
        flash(f"Erreur système : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close()

# CRUD Professeurs
@app.route('/professeurs')
def liste_professeurs():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM professeur ORDER BY nom, prenom")
    professeurs = cur.fetchall()
    cur.close()
    return render_template('professeurs/liste.html', professeurs=professeurs)

@app.route('/professeurs/creer', methods=['GET', 'POST'])
def creer_professeur():
    if request.method == 'POST':
        data = {
            'prenom': request.form['prenom'].strip(),
            'nom': request.form['nom'].strip(),
            'email': request.form.get('email', '').strip(),
            'telephone': request.form.get('telephone', '').strip()
        }

        if not all([data['prenom'], data['nom']]):
            flash("Le prénom et le nom sont obligatoires", "danger")
            return redirect(url_for('creer_professeur'))

        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO professeur (prenom, nom, email, telephone)
                VALUES (%s, %s, %s, %s)
            """, (data['prenom'], data['nom'], data['email'], data['telephone']))
            mysql.connection.commit()
            flash("Professeur créé avec succès", "success")
            return redirect(url_for('liste_professeurs'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur: {str(e)}", "danger")
        finally:
            cur.close()
    return render_template('professeurs/creer.html')

@app.route('/professeurs/editer/<int:id>', methods=['GET', 'POST'])
def editer_professeur(id):
    cur = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            data = {
                'prenom': request.form['prenom'].strip(),
                'nom': request.form['nom'].strip(),
                'email': request.form.get('email', '').strip(),
                'telephone': request.form.get('telephone', '').strip()
            }

            if not all([data['prenom'], data['nom']]):
                flash("Le prénom et le nom sont obligatoires", "danger")
                return redirect(url_for('editer_professeur', id=id))

            cur.execute("""
                UPDATE professeur 
                SET prenom=%s, nom=%s, email=%s, telephone=%s 
                WHERE id_prof=%s
            """, (data['prenom'], data['nom'], data['email'], data['telephone'], id))
            mysql.connection.commit()
            flash("Modifications enregistrées", "success")
            return redirect(url_for('liste_professeurs'))

        cur.execute("SELECT * FROM professeur WHERE id_prof = %s", (id,))
        professeur = cur.fetchone()
        return render_template('professeurs/editer.html', professeur=professeur)

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)}", "danger")
        return redirect(url_for('liste_professeurs'))
    finally:
        cur.close()

@app.route('/professeurs/supprimer/<int:id>', methods=['POST'])
def supprimer_professeur(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM professeur WHERE id_prof = %s", (id,))
        mysql.connection.commit()
        flash("Professeur supprimé", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)} - Des TP sont associés à ce professeur", "danger")
    finally:
        cur.close()
    return redirect(url_for('liste_professeurs'))

# CRUD Matières
@app.route('/matieres/liste')
def liste_matieres():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM matiere ORDER BY nom_matiere")
    matieres = cur.fetchall()
    cur.close()
    return render_template('matieres/liste.html', matieres=matieres)

@app.route('/matieres/creer', methods=['GET', 'POST'])
def creer_matiere():
    if request.method == 'POST':
        nom_matiere = request.form['nom_matiere'].strip()

        if not nom_matiere:
            flash("Le nom de la matière est obligatoire", "danger")
            return redirect(url_for('creer_matiere'))

        cur = mysql.connection.cursor()
        try:
            # Vérifier si la matière existe déjà (insensible à la casse et aux espaces)
            cur.execute("""
                SELECT id_matiere 
                FROM matiere 
                WHERE LOWER(TRIM(nom_matiere)) = LOWER(TRIM(%s))
            """, (nom_matiere,))
            
            if cur.fetchone():
                flash("Cette matière existe déjà", "danger")
                return redirect(url_for('creer_matiere'))

            # Créer la matière si elle n'existe pas
            cur.execute("INSERT INTO matiere (nom_matiere) VALUES (%s)", (nom_matiere,))
            mysql.connection.commit()
            flash("Matière créée avec succès", "success")
            return redirect(url_for('liste_matieres'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur: {str(e)}", "danger")
        finally:
            cur.close()
            
    return render_template('matieres/creer.html')

@app.route('/matieres/editer/<int:id>', methods=['GET', 'POST'])
def editer_matiere(id):
    cur = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            nom_matiere = request.form['nom_matiere'].strip()
            
            if not nom_matiere:
                flash("Le nom de la matière est obligatoire", "danger")
                return redirect(url_for('editer_matiere', id=id))

            # Vérifier les doublons en excluant l'ID courant
            cur.execute("""
                SELECT id_matiere 
                FROM matiere 
                WHERE LOWER(TRIM(nom_matiere)) = LOWER(TRIM(%s))
                AND id_matiere != %s
            """, (nom_matiere, id))
            
            if cur.fetchone():
                flash("Cette matière existe déjà", "danger")
                return redirect(url_for('editer_matiere', id=id))

            # Mettre à jour si pas de doublon
            cur.execute("""
                UPDATE matiere 
                SET nom_matiere = %s 
                WHERE id_matiere = %s
            """, (nom_matiere, id))
            
            mysql.connection.commit()
            flash("Matière mise à jour", "success")
            return redirect(url_for('liste_matieres'))

        # Récupération de la matière pour l'édition
        cur.execute("SELECT * FROM matiere WHERE id_matiere = %s", (id,))
        matiere = cur.fetchone()
        return render_template('matieres/editer.html', matiere=matiere)

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)}", "danger")
        return redirect(url_for('liste_matieres'))
    finally:
        cur.close()

@app.route('/matieres/supprimer/<int:id>', methods=['POST'])
def supprimer_matiere(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM matiere WHERE id_matiere = %s", (id,))
        mysql.connection.commit()
        flash("Matière supprimée", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)} - Des TP utilisent cette matière", "danger")
    finally:
        cur.close()
    return redirect(url_for('liste_matieres'))

# CRUD Laboratoires
@app.route('/laboratoires')
def liste_laboratoires():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM laboratoire ORDER BY nom_laboratoire")
    laboratoires = cur.fetchall()
    cur.close()
    return render_template('laboratoires/liste.html', laboratoires=laboratoires)

@app.route('/laboratoires/creer', methods=['GET', 'POST'])
def creer_laboratoire():
    if request.method == 'POST':
        data = {
            'nom': request.form['nom_laboratoire'].strip(),
            'capacite': request.form.get('capacite', 0) or 0
        }

        if not data['nom']:
            flash("Le nom du laboratoire est obligatoire", "danger")
            return redirect(url_for('creer_laboratoire'))

        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO laboratoire (nom_laboratoire, capacite)
                VALUES (%s, %s)
            """, (data['nom'], data['capacite']))
            mysql.connection.commit()
            flash("Laboratoire créé avec succès", "success")
            return redirect(url_for('liste_laboratoires'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur: {str(e)}", "danger")
        finally:
            cur.close()
    return render_template('laboratoires/creer.html')

@app.route('/laboratoires/editer/<int:id>', methods=['GET', 'POST'])
def editer_laboratoire(id):
    cur = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            data = {
                'nom': request.form['nom_laboratoire'].strip(),
                'capacite': request.form.get('capacite', 0) or 0
            }

            if not data['nom']:
                flash("Le nom du laboratoire est obligatoire", "danger")
                return redirect(url_for('editer_laboratoire', id=id))

            cur.execute("""
                UPDATE laboratoire 
                SET nom_laboratoire=%s, capacite=%s 
                WHERE id_laboratoire=%s
            """, (data['nom'], data['capacite'], id))
            mysql.connection.commit()
            flash("Modifications enregistrées", "success")
            return redirect(url_for('liste_laboratoires'))

        cur.execute("SELECT * FROM laboratoire WHERE id_laboratoire = %s", (id,))
        laboratoire = cur.fetchone()
        return render_template('laboratoires/editer.html', laboratoire=laboratoire)

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)}", "danger")
        return redirect(url_for('liste_laboratoires'))
    finally:
        cur.close()

@app.route('/laboratoires/supprimer/<int:id>', methods=['POST'])
def supprimer_laboratoire(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM laboratoire WHERE id_laboratoire = %s", (id,))
        mysql.connection.commit()
        flash("Laboratoire supprimé", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)} - Des TP utilisent ce laboratoire", "danger")
    finally:
        cur.close()
    return redirect(url_for('liste_laboratoires'))

from datetime import datetime, time, timedelta

def get_period(t):
    """Gère tous les formats temporels entrants"""
    if isinstance(t, str):
        # Conversion depuis un string SQL 'HH:MM:SS'
        t = datetime.strptime(t, '%H:%M:%S').time()
    elif isinstance(t, timedelta):
        # Conversion depuis un timedelta
        total_seconds = t.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        t = time(hours, minutes)
    
    periods = {
        'P1': (time(8, 0), time(9, 30)),
        'P2': (time(9, 45), time(11, 15)),
        'P3': (time(11, 30), time(13, 0)),
        'P4': (time(15, 10), time(16, 40)),
        'P5': (time(17, 0), time(18, 30))
    }
    
    for period, (start, end) in periods.items():
        if start <= t <= end:
            return period
    return None

@app.route('/emploi')
def emploi():
    try:
        lab_id = request.args.get('lab_id', type=int)
        week_offset = int(request.args.get('week_offset', 0))
        today = datetime.today()
        start_date = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        days = [start_date + timedelta(days=i) for i in range(7)]  # Lundi à dimanche

        CRENEAUX = {
            'P1': (time(8, 0), time(9, 30)),
            'P2': (time(9, 45), time(11, 15)),
            'P3': (time(11, 30), time(13, 0)),
            'P4': (time(15, 10), time(16, 40)),
            'P5': (time(17, 0), time(18, 30))
        }

        cur = mysql.connection.cursor()
        
        # Récupération de la liste des laboratoires
        cur.execute("SELECT id_laboratoire, nom_laboratoire FROM laboratoire")
        laboratoires = cur.fetchall()

        # Requête modifiée pour filtrer par labo
        query = """
            SELECT 
                tp.id_tp,
                tp.nom_tp,
                DATE(tp.heure_debut) AS date_tp,
                TIME(tp.heure_debut) AS debut,
                TIME(tp.heure_fin) AS fin,
                p.prenom,
                p.nom,
                m.nom_matiere,
                l.id_laboratoire,
                l.nom_laboratoire
            FROM tp
            JOIN professeur p ON tp.id_prof = p.id_prof
            JOIN matiere m ON tp.id_matiere = m.id_matiere
            LEFT JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
            WHERE YEARWEEK(tp.heure_debut, 1) = YEARWEEK(%s, 1)
        """
        params = [start_date]
        
        if lab_id:
            query += " AND l.id_laboratoire = %s"
            params.append(lab_id)
            
        query += " ORDER BY tp.heure_debut, l.id_laboratoire"
        
        cur.execute(query, tuple(params))

        tps = {}
        for tp in cur.fetchall():
            debut = tp['debut']
            if isinstance(debut, timedelta):
                total_seconds = debut.total_seconds()
                debut = time(int(total_seconds // 3600), int((total_seconds % 3600) // 60))
            
            periode = get_period(debut)
            
            if periode:
                lab_key = f"{tp['id_laboratoire']}-{tp['date_tp'].strftime('%Y-%m-%d')}-{periode}"
                tps[lab_key] = tp

        return render_template('emplois/emploi.html',
                            laboratoires=laboratoires,
                            selected_lab=lab_id,
                            days=days,
                            CRENEAUX=CRENEAUX,
                            tps=tps,
                            week_offset=week_offset)

    except Exception as e:
        flash(f"Erreur système : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        if 'cur' in locals():
            cur.close()
if __name__ == '__main__':
    with app.app_context():
        create_default_users()
    app.run(debug=True)
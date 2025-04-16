import os
from datetime import datetime, timedelta, time as dt_time  # Alias pour datetime.time
import time  # Module time standard
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, render_template_string, json, Response,send_from_directory
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from werkzeug.utils import secure_filename
from flask_session import Session 
from flask_wtf.csrf import CSRFProtect
import locale
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itsdangerous import URLSafeTimedSerializer
import secrets
import smtplib
import re
from flask_mail import Mail, Message

app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = os.environ.get('SECRET_KEY') or 'sidahmed43'  
# Configuration de session 
app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR='/tmp/flask_sessions',  
    SESSION_COOKIE_NAME='lab_session',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False, 
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)
Session(app)
# Configuration MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gestion_lab'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MAIL_SUPPRESS_SEND'] = False  # Activer l'envoi réel
app.config['MAIL_DEBUG'] = False

mysql = MySQL(app)

# Configuration Mailjet
app.config.update(
    MAIL_SERVER='in-v3.mailjet.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='8559250c64a2ffb049cd789fc94c2b67',  # À récupérer sur le dashboard Mailjet
    MAIL_PASSWORD='69a105021dc70ca8f5a0934b3f4a1280',  # À récupérer sur le dashboard Mailjet
    MAIL_DEFAULT_SENDER=('LabManager', '23535@isme.esp.mr')
)

mail = Mail(app)

# Configuration
UPLOAD_FOLDER = 'static/sds'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



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
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'user') NOT NULL DEFAULT 'user'
                      )
                 """)
                print("Table utilisateur créée")

            # Créer admin
            cur.execute("SELECT * FROM utilisateur WHERE username = 'admin'")
            if not cur.fetchone():
              hashed_pw = generate_password_hash('admin123')
              cur.execute("""
                INSERT INTO utilisateur (username, email, password, role) 
                VALUES (%s, %s, %s, 'admin')
            """, ('admin', 'admin@example.com', hashed_pw))
              print("Admin créé")

            # Créer user
            cur.execute("SELECT * FROM utilisateur WHERE username = 'user'")
            if not cur.fetchone():
                hashed_pw = generate_password_hash('user123')
                cur.execute("""
                    INSERT INTO utilisateur (username, email, password) 
                    VALUES (%s, %s, %s)
                """, ('user', 'user@example.com', hashed_pw))
                print("User créé")

            mysql.connection.commit()
        except Exception as e:
            print(f"ERREUR CRITIQUE : {str(e)}")
            raise  # Propager l'erreur pour la voir dans les logs
        finally:
            cur.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM utilisateur WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()
            
            if user:
                # Vérification si le compte est désactivé
                if not user['is_active']:
                    flash('Ce compte est désactivé', 'danger')
                    return redirect(url_for('login'))
                
                if check_password_hash(user['password'], password):
                    session.clear()
                    session['user_id'] = user['id']
                    session['email'] = user['email']
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
    # Liste des routes protégées (nécessitant une connexion)
    protected_routes = [
        'index', 'liste_professeurs', 'creer_tp', 'editer_tp',
        'supprimer_tp', 'creer_recu', 'liste_matieres', 'creer_matiere',
        'editer_matiere', 'supprimer_matiere', 'liste_laboratoires',
        'creer_laboratoire', 'editer_laboratoire', 'supprimer_laboratoire'
    ]
    
    # Vérification de la connexion
    if request.endpoint in protected_routes and not session.get('user_id'):
        return redirect(url_for('login'))
    
    # Vérification des droits admin/super_admin
    admin_only_routes = [
        'creer_professeur', 'supprimer_professeur',
        'creer_matiere', 'supprimer_matiere',
        'creer_laboratoire', 'supprimer_laboratoire'
    ]
    
    if request.endpoint in admin_only_routes:
        if session.get('role') not in ['admin', 'super_admin']:
            abort(403)  # Accès interdit
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.before_request
def verify_access():
    excluded = ['login', 'static', 'logout','forgot_password','verify_code', 'reset_password']
    
    if request.endpoint in excluded:
        return
    
    # Vérifier si l'utilisateur est connecté
    if 'user_id' not in session:
        print("Redirection vers login - Session invalide")
        return redirect(url_for('login'))
    
    # Vérifier si l'utilisateur existe toujours dans la base de données
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM utilisateur WHERE id = %s", (user_id,))
    user_exists = cur.fetchone()
    cur.close()
    
    if not user_exists:
        session.clear()
        flash("Votre compte a été supprimé.", "danger")
        return redirect(url_for('login'))
    
    # Vérifier les droits admin pour les routes concernées
    admin_only_routes = [
        'creer_professeur', 'supprimer_professeur',
        'creer_matiere', 'supprimer_matiere',
        'creer_laboratoire', 'supprimer_laboratoire',
        'liste_utilisateurs', 'creer_utilisateur', 
        'editer_utilisateur', 'supprimer_utilisateur',
    ]
    
    if request.endpoint in admin_only_routes and session.get('role') not in ['admin', 'super_admin']:
        abort(403, description="Accès réservé aux administrateurs")
    
    # Maintenir la session active
    session.permanent = True
    session.modified = True

    def verify_admin_access():
        if request.endpoint in ['parametres', 'request_admin_code', 'verify_admin_access']:
            if not session.get('admin_verified'):
                return redirect(url_for('verify_admin_access'))

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html', description=e.description), 403

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    show_welcome = session.pop('show_welcome', False)

    CRENEAUX = {
        'P1': ('08:00', '09:30'),
        'P2': ('09:45', '11:15'),
        'P3': ('11:30', '13:00'),
        'P4': ('15:10', '16:40'),
        'P5': ('17:00', '18:30')
    }

    try:
        cur = mysql.connection.cursor()
        
        today = datetime.now().date()
        cur.execute("""
            SELECT 
                tp.id_tp,
                tp.nom_tp,
                tp.heure_debut,
                tp.heure_fin,
                CONCAT(p.prenom, ' ', p.nom) AS professeur,
                m.nom_matiere AS matiere,
                m.niveau,
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
            start_dt = tp['heure_debut']
            end_dt = tp['heure_fin']
            start_time = start_dt.strftime('%H:%M')
            end_time = end_dt.strftime('%H:%M')
            
            periode = None
            for key, (s, e) in CRENEAUX.items():
                if s == start_time and e == end_time:
                    periode = key
                    break
            
            tps_jour.append({
                **tp,
                'statut': get_tp_status(start_dt.time(), end_dt.time()),
                'periode': periode,
                'heure_debut': start_time,
                'heure_fin': end_time
            })
        # Alertes stock
        cur.execute("""
                SELECT 
                    a.nom_article,
                    a.unite_mesure,
                    sm.quantite
                FROM stock_magasin sm
                JOIN article a ON sm.id_article = a.id_article  # ✅ Correction ici
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
    lab_id = request.args.get('lab_id', None, type=int)
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
    
    return redirect(url_for('emploi', lab_id=lab_id, week_offset=redirect_week))

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
    cur.execute("SELECT id_matiere, nom_matiere, niveau FROM matiere")  # Ajouter niveau
    matieres = cur.fetchall()
    cur.execute("SELECT id_laboratoire, nom_laboratoire FROM laboratoire")
    laboratoires = cur.fetchall()
    cur.close()

    now = datetime.now()
    current_year = now.year
    default_annee = "2024-2025"
    if now.month >= 10:
        default_annee = f"{current_year + 1}-{current_year + 2}"
    else:
        pass
    if request.method == 'POST':
        try:
            data = {
                'nom_tp': request.form['nom_tp'].strip(),
                'id_prof': request.form.get('id_prof', '').strip(),
                'id_matiere': request.form.get('id_matiere', '').strip(),
                'id_laboratoire': request.form.get('id_laboratoire', '').strip(),
                'date_tp': request.form['date_tp'].strip(),
                'periodes': request.form.getlist('periodes'),
                'annee_scolaire': request.form['annee_scolaire'].strip(),
                'annee_scolaire': default_annee  # On utilise la valeur calculée

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
                    # 1. Vérification conflit professeur
                    cur.execute("""
                        SELECT id_tp 
                        FROM tp 
                        WHERE (
                            (heure_debut < %s AND heure_fin > %s) OR
                            (heure_debut BETWEEN %s AND %s) OR
                            (heure_fin BETWEEN %s AND %s)
                        )
                        AND id_prof = %s
                    """, (
                        heure_fin, heure_debut,
                        heure_debut, heure_fin,
                        heure_debut, heure_fin,
                        data['id_prof']
                    ))
                    if cur.fetchone():
                        flash(f"Le professeur est déjà occupé ({periode} {debut}-{fin}) !", "danger")
                        mysql.connection.rollback()
                        return render_template('creer_tp.html',
                                            professeurs=professeurs,
                                            matieres=matieres,
                                            CRENEAUX=CRENEAUX,
                                            laboratoires=laboratoires,
                                            from_emploi=from_emploi,
                                            default_date=default_date)
                    
                    # 2. Vérification conflit laboratoire (nouveau)
                    cur.execute("""
                        SELECT id_tp 
                        FROM tp 
                        WHERE (
                            (heure_debut < %s AND heure_fin > %s) OR
                            (heure_debut BETWEEN %s AND %s) OR
                            (heure_fin BETWEEN %s AND %s)
                        )
                        AND id_laboratoire = %s
                    """, (
                        heure_fin, heure_debut,
                        heure_debut, heure_fin,
                        heure_debut, heure_fin,
                        data['id_laboratoire']
                    ))
                    if cur.fetchone():
                        flash(f"Le labo est déjà réservé ({periode} {debut}-{fin}) !", "danger")
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
                        default_annee=default_annee,
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

    lab_id = request.args.get('lab_id', None, type=int)
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
                                AND id_tp != %s  /* Exclusion du TP actuel */
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
        return redirect(url_for('emploi', lab_id=lab_id, week_offset=redirect_week))
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

# CRUD Professeurs
@app.route('/professeurs')
def liste_professeurs():  
    cur = mysql.connection.cursor()
    
    # Version avec filtre actif
    cur.execute("""
        SELECT p.*, COUNT(tp.id_tp) as tp_count 
        FROM professeur p
        LEFT JOIN tp ON p.id_prof = tp.id_prof 
            AND DATE(tp.heure_debut) = CURDATE()
        GROUP BY p.id_prof
        HAVING tp_count > 0
        ORDER BY p.nom, p.prenom
    """)
    
    professeurs = cur.fetchall()
    tp_counts = {prof['id_prof']: prof['tp_count'] for prof in professeurs}
    cur.close()
    
    return render_template('professeurs/liste.html',
                         professeurs=professeurs,
                         tp_counts=tp_counts,
                         now=datetime.now(),
                         active_filter=True)

@app.route('/professeurs/all')
def tous_les_professeurs():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM professeur ORDER BY nom, prenom")
    professeurs = cur.fetchall()
    cur.close()
    return render_template('professeurs/liste.html', 
                         professeurs=professeurs,
                         all_profs=True,
                         now=datetime.now())

@app.route('/professeurs/creer', methods=['GET', 'POST'])
def creer_professeur():
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
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
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
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
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
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
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
    if request.method == 'POST':
        nom_matiere = request.form['nom_matiere'].strip()
        niveau = request.form['niveau']  # Récupération du niveau

        if not nom_matiere or not niveau:
            flash("Tous les champs obligatoires doivent être remplis", "danger")
            return redirect(url_for('creer_matiere'))

        cur = mysql.connection.cursor()
        try:
            # Vérification des doublons avec niveau
            cur.execute("""
                SELECT id_matiere 
                FROM matiere 
                WHERE LOWER(TRIM(nom_matiere)) = LOWER(TRIM(%s))
                AND niveau = %s
            """, (nom_matiere, niveau))
            
            if cur.fetchone():
                flash("Cette matière existe déjà pour ce niveau", "danger")
                return redirect(url_for('creer_matiere'))

            # Insertion avec niveau
            cur.execute("""
                INSERT INTO matiere (nom_matiere, niveau) 
                VALUES (%s, %s)
            """, (nom_matiere, niveau))
            
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
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
    cur = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            nom_matiere = request.form['nom_matiere'].strip()
            niveau = request.form['niveau']  # Récupération du niveau
            
            if not nom_matiere or not niveau:
                flash("Tous les champs obligatoires doivent être remplis", "danger")
                return redirect(url_for('editer_matiere', id=id))

            # Vérification des doublons avec niveau
            cur.execute("""
                SELECT id_matiere 
                FROM matiere 
                WHERE LOWER(TRIM(nom_matiere)) = LOWER(TRIM(%s))
                AND niveau = %s
                AND id_matiere != %s
            """, (nom_matiere, niveau, id))
            
            if cur.fetchone():
                flash("Cette matière existe déjà pour ce niveau", "danger")
                return redirect(url_for('editer_matiere', id=id))

            # Mise à jour avec niveau
            cur.execute("""
                UPDATE matiere 
                SET nom_matiere = %s, 
                    niveau = %s 
                WHERE id_matiere = %s
            """, (nom_matiere, niveau, id))
            
            mysql.connection.commit()
            flash("Matière mise à jour", "success")
            return redirect(url_for('liste_matieres'))

        # Récupération de la matière avec niveau
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
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
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
@app.route('/laboratoires/actifs')
def laboratoires_actifs():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT l.*, COUNT(tp.id_tp) as tp_count 
        FROM laboratoire l
        LEFT JOIN tp ON l.id_laboratoire = tp.id_laboratoire 
            AND DATE(tp.heure_debut) = CURDATE()
        GROUP BY l.id_laboratoire
        HAVING tp_count > 0
        ORDER BY l.nom_laboratoire
    """)
    laboratoires = cur.fetchall()
    tp_counts = {lab['id_laboratoire']: lab['tp_count'] for lab in laboratoires}
    cur.close()
    return render_template('laboratoires/liste.html',
                         laboratoires=laboratoires,
                         tp_counts=tp_counts,
                         active_filter=True,
                         now=datetime.now())

@app.route('/laboratoires/all')
def tous_les_laboratoires():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM laboratoire ORDER BY nom_laboratoire")
    laboratoires = cur.fetchall()
    cur.close()
    return render_template('laboratoires/liste.html',
                         laboratoires=laboratoires,
                         active_filter=False,
                         now=datetime.now())


@app.route('/laboratoires/creer', methods=['GET', 'POST'])
def creer_laboratoire():
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
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
            return redirect(url_for('laboratoires_actifs'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur: {str(e)}", "danger")
        finally:
            cur.close()
    return render_template('laboratoires/creer.html')

@app.route('/laboratoires/editer/<int:id>', methods=['GET', 'POST'])
def editer_laboratoire(id):
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
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
            return redirect(url_for('laboratoires_actifs'))

        cur.execute("SELECT * FROM laboratoire WHERE id_laboratoire = %s", (id,))
        laboratoire = cur.fetchone()
        return render_template('laboratoires/editer.html', laboratoire=laboratoire)

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur: {str(e)}", "danger")
        return redirect(url_for('laboratoires_actifs'))
    finally:
        cur.close()

@app.route('/laboratoires/supprimer/<int:id>', methods=['POST'])
def supprimer_laboratoire(id):
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
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
    return redirect(url_for('laboratoires_actifs'))

def get_period(t):
    """Gère tous les formats temporels entrants"""
    # Conversion vers datetime.time
    if isinstance(t, str):
        # Conversion depuis un string SQL 'HH:MM:SS'
        t = datetime.strptime(t, '%H:%M:%S').time()
    elif isinstance(t, timedelta):
        # Conversion depuis un timedelta
        total_seconds = t.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        t = dt_time(hours, minutes)  # Utilisation de l'alias
    
    # Définition des périodes avec le bon type
    periods = {
        'P1': (dt_time(8, 0), dt_time(9, 30)),
        'P2': (dt_time(9, 45), dt_time(11, 15)),
        'P3': (dt_time(11, 30), dt_time(13, 0)),
        'P4': (dt_time(15, 10), dt_time(16, 40)),
        'P5': (dt_time(17, 0), dt_time(18, 30))
    }
    
    # Vérification des plages horaires
    for period, (start, end) in periods.items():
        if start <= t <= end:
            return period
    return None

@app.route('/emploi')
def emploi():
    try:
        if request.method == 'HEAD':
            return Response()
        
        # Configuration locale française
        locale.setlocale(locale.LC_TIME, 'french')

        # Récupération des paramètres
        lab_id = request.args.get('lab_id', type=int)
        week_offset = int(request.args.get('week_offset', 0))
        
        # Calcul des dates
        today = datetime.today()
        start_date = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        days = [start_date + timedelta(days=i) for i in range(7)]  # Lundi à dimanche

        # Définition des créneaux horaires avec datetime.time
        CRENEAUX = {
            'P1': (dt_time(8, 0), dt_time(9, 30)),
            'P2': (dt_time(9, 45), dt_time(11, 15)),
            'P3': (dt_time(11, 30), dt_time(13, 0)),
            'P4': (dt_time(15, 10), dt_time(16, 40)),
            'P5': (dt_time(17, 0), dt_time(18, 30))
        }

        # Connexion à la base de données
        cur = mysql.connection.cursor()
        
        # Récupération des laboratoires
        cur.execute("SELECT id_laboratoire, nom_laboratoire FROM laboratoire")
        laboratoires = cur.fetchall()
        
        # Requête des TPs
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

        # Traitement des résultats
        tps = {}
        for tp in cur.fetchall():
            debut = tp['debut']
            
            # Conversion si nécessaire
            if isinstance(debut, timedelta):
                total_seconds = debut.total_seconds()
                debut = dt_time(int(total_seconds // 3600), int((total_seconds % 3600) // 60))
            
            periode = get_period(debut)  # Supposons que cette fonction utilise datetime.time
            
            if periode:
                lab_key = f"{tp['id_laboratoire']}-{tp['date_tp'].strftime('%Y-%m-%d')}-{periode}"
                tps[lab_key] = tp

        return render_template('emplois/emploi.html',
                            current_time=datetime.now().strftime('%d/%m/%Y à %H:%M'),
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

@app.route('/emploi/print')
def print_emploi():
    try:
        lab_id = request.args.get('lab_id', type=int)
        week_offset = int(request.args.get('week_offset', 0))
        
        # Calcul des dates (identique à la route emploi)
        today = datetime.today()
        start_date = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        days = [start_date + timedelta(days=i) for i in range(7)]

        cur = mysql.connection.cursor()
        
        # Récupération nom labo
        lab_name = "Tous les laboratoires"
        if lab_id:
            cur.execute("SELECT nom_laboratoire FROM laboratoire WHERE id_laboratoire = %s", (lab_id,))
            lab = cur.fetchone()
            lab_name = lab['nom_laboratoire'] if lab else lab_name

        # Requête identique à la route emploi
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
        tps_raw = cur.fetchall()

        # Transformation des données comme dans la route emploi
        tps = {}
        for tp in tps_raw:
            debut = tp['debut']
            if isinstance(debut, timedelta):
                total_seconds = debut.total_seconds()
                debut = time(int(total_seconds // 3600), int((total_seconds % 3600) // 60))
            
            periode = None
            for p, (s, e) in CRENEAUX.items():
                start_time = datetime.strptime(s, "%H:%M").time()
                end_time = datetime.strptime(e, "%H:%M").time()
                if start_time <= debut <= end_time:
                    periode = p
                    break
            
            if periode:
                date_str = tp['date_tp'].strftime('%Y-%m-%d')
                lab_key = f"{tp['id_laboratoire']}-{date_str}-{periode}" if tp['id_laboratoire'] else f"{date_str}-{periode}"
                tps[lab_key] = tp

        return render_template('emplois/emploi_print.html',
                            lab_name=lab_name,
                            days=days,
                            CRENEAUX=CRENEAUX,
                            tps=tps,
                            current_time=datetime.now().strftime('%d/%m/%Y %H:%M'),
                            lab_id=lab_id)

    except Exception as e:
        flash(f"Erreur système : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        if 'cur' in locals():
            cur.close()
            
@app.route('/stocks')
def stocks_overview():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Récupération données magasin
        cur.execute("""
            SELECT COUNT(DISTINCT sm.id_article) as nb_articles, 
                SUM(sm.quantite) as total_quantite
            FROM stock_magasin sm
            WHERE sm.date_expiration IS NULL OR sm.date_expiration > NOW()
        """)
        magasin = cur.fetchone()
        
        # Récupération données labos (CORRECTION ICI)
        cur.execute("""
            SELECT l.id_laboratoire, l.nom_laboratoire, 
                COUNT(DISTINCT sm.id_article) as nb_articles,
                SUM(sl.quantite) as total_quantite
            FROM laboratoire l
            LEFT JOIN stock_laboratoire sl ON l.id_laboratoire = sl.id_laboratoire
            LEFT JOIN stock_magasin sm ON sl.id_lot = sm.id_lot
            GROUP BY l.id_laboratoire
        """)
        laboratoires = cur.fetchall()
        
        return render_template('stock/stock.html',
                            magasin=magasin,
                            laboratoires=laboratoires)
        
    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close() if 'cur' in locals() else None

@app.route('/stock_magasin')
def stock_magasin():
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    # Initialisation des variables avec des valeurs par défaut
    stock = []
    categories = []
    types = []
    cur = None

    try:
        cur = mysql.connection.cursor()
        
        # Requête pour le stock
        cur.execute("""
            SELECT 
                sm.id_lot, 
                a.id_article, 
                a.nom_article, 
                a.unite_mesure,
                sm.quantite, 
                sm.date_expiration, 
                sm.date_ajout,
                t.id_type, 
                t.nom_type, 
                c.id_categorie, 
                c.nom_categorie,
                a.ghs_codes,
                a.sds_filename  
            FROM stock_magasin sm
            JOIN article a ON sm.id_article = a.id_article
            JOIN type t ON a.id_type = t.id_type
            JOIN categorie c ON t.id_categorie = c.id_categorie
            ORDER BY sm.date_expiration ASC
        """)
        stock = cur.fetchall()

        # Requête pour les catégories
        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()

        # Requête pour les types
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()

        print("=== DEBUG STOCK DATA ===")
        for item in stock:
            print(f"Article: {item['nom_article']}")
            print(f"GHS Codes: {item.get('ghs_codes', 'NON RENSEIGNÉ')}")
            print("-------------------")

    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
    finally:
        if cur:
            cur.close()

    return render_template('stock/stock_magasin.html',
                         stock=stock,
                         categories=categories,
                         types=types,)


# Route pour ajouter un article
@app.route('/ajouter_article', methods=['GET', 'POST'])
def ajouter_article():
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))

    # Configuration des pictogrammes
    pictograms = [
        ('01', 'GHS01', 'Corrosif'),
        ('02', 'GHS02', 'Danger environnement'),
        ('03', 'GHS03', 'gaz sous pression'),
        ('04', 'GHS04', 'Nocif ou irritant'),
        ('05', 'GHS05', 'Explosif'),
        ('06', 'GHS06', 'Inflammable'),
        ('07', 'GHS07', 'Comburant'),
        ('08', 'GHS08', 'Danger pour la santé'),
        ('09', 'GHS09', 'Toxique')
    ]

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()

        if request.method == 'POST':
            required_fields = ['nom', 'unite', 'quantite', 'type']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f"Le champ {field} est requis", "danger")
                    return redirect(url_for('ajouter_article'))

            nom = request.form['nom'].strip()
            unite = request.form['unite']
            quantite = int(request.form['quantite'])
            id_type = int(request.form['type'])
            date_expiration = request.form.get('date_expiration') or None
            ghs_codes = ','.join(request.form.getlist('ghs_codes'))
            sds_filename = None

            # Gestion du fichier SDS
            sds_file = request.files.get('sds')
            if sds_file and sds_file.filename != '':
                if not allowed_file(sds_file.filename):
                    flash("Seuls les fichiers PDF sont acceptés", "danger")
                    return redirect(url_for('ajouter_article'))
                
                filename = secure_filename(sds_file.filename)
                unique_id = uuid.uuid4().hex[:8]
                sds_filename = f"{unique_id}_{filename}"
                sds_file.save(os.path.join(app.config['UPLOAD_FOLDER'], sds_filename))

            try:
                with mysql.connection.cursor() as trans_cur:
                    # Insertion article
                    trans_cur.execute("""
                        INSERT INTO article (
                            nom_article, unite_mesure, id_type, 
                            date_expiration, ghs_codes, sds_filename
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (nom, unite, id_type, date_expiration, ghs_codes, sds_filename))
                    
                    id_article = trans_cur.lastrowid

                    # Insertion stock
                    trans_cur.execute("""
                        INSERT INTO stock_magasin (
                            id_article, quantite, date_expiration
                        ) VALUES (%s, %s, %s)
                    """, (id_article, quantite, date_expiration))
                    
                    mysql.connection.commit()
                    flash("Article créé avec succès", "success")
                    return redirect(url_for('stock_magasin'))

            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur base de données : {str(e)}", "danger")
        return render_template('stock/ajouter_article.html',
                            categories=categories,
                            types=types,
                            pictograms=pictograms)

    except Exception as e:
        flash(f"Erreur système : {str(e)}", "danger")
        return redirect(url_for('stock_magasin'))
    
    finally:
        if 'cur' in locals(): 
            cur.close()
# Route pour éditer un article
@app.route('/editer_article/<int:id>', methods=['GET', 'POST'])
def editer_article(id):
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))

    pictograms = [
        ('01', 'GHS01', 'Explosif'),
        ('02', 'GHS02', 'Inflammable'),
        ('03', 'GHS03', 'Comburant'),
        ('05', 'GHS05', 'Corrosif'),
        ('06', 'GHS06', 'Toxique'),
        ('08', 'GHS08', 'Danger santé'),
        ('09', 'GHS09', 'Danger environnement')
    ]

    try:
        cur = mysql.connection.cursor()

        if request.method == 'POST':
            # Validation des champs obligatoires
            required_fields = ['nom', 'unite', 'quantite', 'type']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f"Le champ {field} est requis", "danger")
                    return redirect(url_for('editer_article', id=id))

            # Extraction des données
            nom = request.form['nom'].strip()
            unite = request.form['unite']
            quantite = int(request.form['quantite'])
            id_type = int(request.form['type'])
            date_expiration = request.form.get('date_expiration') or None
            ghs_codes = ','.join(request.form.getlist('ghs_codes'))
            sds_file = request.files.get('sds')

            # Récupération ancien fichier
            cur.execute("SELECT sds_filename FROM article WHERE id_article = %s", (id,))
            existing_sds = cur.fetchone()['sds_filename']
            sds_filename = existing_sds

            # Gestion du nouveau fichier
            new_file_uploaded = False
            if sds_file and sds_file.filename != '':
                if not allowed_file(sds_file.filename):
                    flash("Format de fichier non autorisé (PDF uniquement)", "danger")
                    return redirect(url_for('editer_article', id=id))

                # Génération nouveau nom de fichier
                filename = secure_filename(sds_file.filename)
                unique_id = uuid.uuid4().hex[:8]
                sds_filename = f"{unique_id}_{filename}"
                new_file_uploaded = True

            try:
                with mysql.connection.cursor() as trans_cur:
                    # Mise à jour base de données
                    trans_cur.execute("""
                        UPDATE article SET
                            nom_article = %s,
                            unite_mesure = %s,
                            id_type = %s,
                            date_expiration = %s,
                            ghs_codes = %s,
                            sds_filename = %s
                        WHERE id_article = %s
                    """, (nom, unite, id_type, date_expiration, ghs_codes, sds_filename, id))

                    trans_cur.execute("""
                        UPDATE stock_magasin 
                        SET quantite = %s,
                            date_expiration = %s
                        WHERE id_article = %s
                        ORDER BY date_expiration ASC
                        LIMIT 1
                    """, (quantite, date_expiration, id))

                    mysql.connection.commit()

                    # Gestion fichiers après commit réussi
                    if new_file_uploaded:
                        # Suppression ancien fichier
                        if existing_sds:
                            old_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_sds)
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        
                        # Sauvegarde nouveau fichier
                        sds_file.save(os.path.join(app.config['UPLOAD_FOLDER'], sds_filename))

                    flash("Article mis à jour avec succès", "success")
                    return redirect(url_for('stock_magasin'))

            except Exception as e:
                mysql.connection.rollback()
                # Nettoyage fichier en cas d'erreur
                if new_file_uploaded and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], sds_filename)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], sds_filename))
                raise e

        # Récupération données existantes
        cur.execute("""
            SELECT 
                a.*, 
                sm.quantite, 
                sm.date_expiration,
                t.id_categorie 
            FROM article a
            JOIN stock_magasin sm ON a.id_article = sm.id_article
            JOIN type t ON a.id_type = t.id_type
            WHERE a.id_article = %s
            LIMIT 1
        """, (id,))
        article = cur.fetchone()

        current_ghs = set(article['ghs_codes'].split(',')) if article['ghs_codes'] else set()

        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()

        return render_template('stock/editer_article.html',
                            article=article,
                            categories=categories,
                            types=types,
                            pictograms=pictograms,
                            current_ghs=current_ghs)

    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for('stock_magasin'))
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/supprimer_article/<int:id>', methods=['POST'])
def supprimer_article(id):
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))

    try:
        with mysql.connection.cursor() as trans_cur:
            # Récupération du fichier SDS
            trans_cur.execute("SELECT sds_filename FROM article WHERE id_article = %s", (id,))
            sds_filename = trans_cur.fetchone()['sds_filename']

            # Suppression fichier physique
            if sds_filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], sds_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Suppression en cascade
            trans_cur.execute("DELETE FROM stock_laboratoire WHERE id_lot IN (SELECT id_lot FROM stock_magasin WHERE id_article = %s)", (id,))
            trans_cur.execute("DELETE FROM stock_magasin WHERE id_article = %s", (id,))
            trans_cur.execute("DELETE FROM article WHERE id_article = %s", (id,))
            
            mysql.connection.commit()
            flash("Article et stocks associés supprimés", "success")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur : {str(e)}", "danger")
    
    return redirect(url_for('stock_magasin'))



# Route pour le stock laboratoire
@app.route('/laboratoires/<int:id_lab>/stock', methods=['GET', 'POST'])
def stock_laboratoire(id_lab):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    try:
        # Récupération labo
        cur.execute("SELECT * FROM laboratoire WHERE id_laboratoire = %s", (id_lab,))
        labo = cur.fetchone()

        # Récupération des catégories et types
        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()
        
        # Création des dictionnaires de correspondance
        type_categories = {t['id_type']: t['id_categorie'] for t in types}
        categories_dict = {c['id_categorie']: c['nom_categorie'] for c in categories}
        types_dict = {t['id_type']: t['nom_type'] for t in types}

        if request.method == 'POST':
            article_id = request.form['article_id']
            quantite = int(request.form['quantite'])
            action = request.form['action']
            
            try:
                with mysql.connection.cursor() as trans_cur:
                    if action == 'ajouter':
                        # Logique d'ajout inchangée
                        trans_cur.execute("""
                            SELECT sm.id_lot, sm.quantite 
                            FROM stock_magasin sm
                            WHERE sm.id_article = %s 
                            AND (sm.date_expiration IS NULL OR sm.date_expiration > NOW())
                            ORDER BY sm.date_expiration ASC
                            LIMIT 1
                            FOR UPDATE
                        """, (article_id,))
                        lot = trans_cur.fetchone()
                        
                        if not lot or lot['quantite'] < quantite:
                            raise Exception("Stock magasin insuffisant ou expiré")

                        trans_cur.execute("""
                            UPDATE stock_magasin
                            SET quantite = quantite - %s
                            WHERE id_lot = %s
                        """, (quantite, lot['id_lot']))
                        
                        trans_cur.execute("""
                            INSERT INTO stock_laboratoire (id_lot, id_laboratoire, quantite)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE quantite = quantite + VALUES(quantite)
                        """, (lot['id_lot'], id_lab, quantite))

                    elif action == 'retirer':
                        # CORRECTION : Récupération du lot depuis le stock du labo
                        trans_cur.execute("""
                            SELECT sl.id_lot, sl.quantite 
                            FROM stock_laboratoire sl
                            JOIN stock_magasin sm ON sl.id_lot = sm.id_lot
                            WHERE sl.id_laboratoire = %s 
                            AND sm.id_article = %s
                            LIMIT 1
                            FOR UPDATE
                        """, (id_lab, article_id))
                        lot = trans_cur.fetchone()
                        
                        if not lot:
                            raise Exception("Article non présent dans le stock du labo")
                            
                        if lot['quantite'] < quantite:
                            raise Exception("Quantité insuffisante en stock labo")

                        # Mise à jour du stock labo
                        trans_cur.execute("""
                            UPDATE stock_laboratoire
                            SET quantite = quantite - %s
                            WHERE id_lot = %s AND id_laboratoire = %s
                        """, (quantite, lot['id_lot'], id_lab))
                        
                        # Remise en stock magasin
                        trans_cur.execute("""
                            UPDATE stock_magasin
                            SET quantite = quantite + %s
                            WHERE id_lot = %s
                        """, (quantite, lot['id_lot']))

                    mysql.connection.commit()
                    flash("Opération réussie", "success")

            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur : {str(e)}", "danger")

        # Récupération du stock avec type et catégorie
        cur.execute("""
            SELECT 
                sl.id_lot,
                a.id_article,
                a.nom_article,
                a.unite_mesure,
                sl.quantite,
                a.id_type,
                t.id_categorie,
                a.ghs_codes
            FROM stock_laboratoire sl
            JOIN stock_magasin sm ON sl.id_lot = sm.id_lot
            JOIN article a ON sm.id_article = a.id_article
            JOIN type t ON a.id_type = t.id_type
            WHERE sl.id_laboratoire = %s
        """, (id_lab,))
        stock = cur.fetchall()

        # Récupération des articles disponibles
        cur.execute("""
            SELECT 
                sm.id_lot,
                a.id_article,
                a.nom_article,
                a.unite_mesure,
                sm.quantite AS stock_disponible,
                a.id_type,
                t.id_categorie
            FROM stock_magasin sm
            JOIN article a ON sm.id_article = a.id_article
            JOIN type t ON a.id_type = t.id_type
            WHERE sm.quantite > 0
            AND (sm.date_expiration IS NULL OR sm.date_expiration > NOW())
        """)
        articles = cur.fetchall()

        return render_template('stock/stock_lab.html',
                            labo=labo,
                            stock=stock,
                            articles=articles,
                            categories=categories,
                            types=types,
                            type_categories=type_categories,
                            categories_dict=categories_dict,
                            types_dict=types_dict)

    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close()


@app.route('/parametres_stock')
def parametres_stock():
  
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    cur = mysql.connection.cursor()
    try:
        # Récupération des catégories
        cur.execute("""
            SELECT c.*,
                (SELECT COUNT(*) FROM type t WHERE t.id_categorie = c.id_categorie) AS nb_types
            FROM categorie c
            ORDER BY c.nom_categorie
        """)
        categories = cur.fetchall()
        
        # Récupération des types avec leurs catégories
        cur.execute("""
            SELECT t.*, c.nom_categorie,
                (SELECT COUNT(*) FROM article a WHERE a.id_type = t.id_type) AS nb_articles
            FROM type t
            JOIN categorie c ON t.id_categorie = c.id_categorie
            ORDER BY c.nom_categorie, t.nom_type
        """)
        types = cur.fetchall()
        
    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close()
    
    return render_template('stock/parametres_stock.html',
                         categories=categories,
                         types=types)

@app.route('/ajouter_categorie', methods=['POST'])
def ajouter_categorie():
 
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    try:
        nom_categorie = request.form['nom_categorie'].strip()
        
        if not nom_categorie:
            flash("Le nom de la catégorie ne peut pas être vide", "danger")
            return redirect(url_for('parametres_stock'))
        
        # Vérification de l'unicité
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categorie WHERE nom_categorie = %s", (nom_categorie,))
        if cur.fetchone():
            flash("Cette catégorie existe déjà", "warning")
            return redirect(url_for('parametres_stock'))
        
        # Insertion de la nouvelle catégorie
        cur.execute("INSERT INTO categorie (nom_categorie) VALUES (%s)", (nom_categorie,))
        mysql.connection.commit()
        flash(f"Catégorie '{nom_categorie}' créée avec succès", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la création de la catégorie : {str(e)}", "danger")
    finally:
        cur.close() if 'cur' in locals() else None
    
    return redirect(url_for('parametres_stock'))

@app.route('/editer_categorie/<int:id>', methods=['POST'])
def editer_categorie(id):
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    try:
        nom_categorie = request.form['nom_categorie'].strip()
        
        if not nom_categorie:
            flash("Le nom de la catégorie ne peut pas être vide", "danger")
            return redirect(url_for('parametres_stock'))
        
        # Vérification de l'unicité (sauf pour l'élément en cours)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categorie WHERE nom_categorie = %s AND id_categorie != %s", 
                    (nom_categorie, id))
        if cur.fetchone():
            flash("Ce nom de catégorie est déjà utilisé", "warning")
            return redirect(url_for('parametres_stock'))
        
        # Mise à jour de la catégorie
        cur.execute("UPDATE categorie SET nom_categorie = %s WHERE id_categorie = %s", 
                    (nom_categorie, id))
        mysql.connection.commit()
        flash(f"Catégorie modifiée avec succès", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la modification de la catégorie : {str(e)}", "danger")
    finally:
        cur.close() if 'cur' in locals() else None
    
    return redirect(url_for('parametres_stock'))

@app.route('/supprimer_categorie/<int:id>', methods=['POST'])
def supprimer_categorie(id):
   
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Vérification des dépendances
        cur.execute("SELECT COUNT(*) as nb_types FROM type WHERE id_categorie = %s", (id,))
        result = cur.fetchone()
        
        if result['nb_types'] > 0:
            flash(f"Impossible de supprimer cette catégorie : {result['nb_types']} type(s) associé(s)", "danger")
            return redirect(url_for('parametres_stock'))
        
        # Suppression
        cur.execute("DELETE FROM categorie WHERE id_categorie = %s", (id,))
        mysql.connection.commit()
        flash("Catégorie supprimée avec succès", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la suppression de la catégorie : {str(e)}", "danger")
    finally:
        cur.close() if 'cur' in locals() else None
    
    return redirect(url_for('parametres_stock'))

@app.route('/ajouter_type', methods=['POST'])
def ajouter_type():
  
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    try:
        nom_type = request.form['nom_type'].strip()
        id_categorie = int(request.form['id_categorie'])
        
        if not nom_type:
            flash("Le nom du type ne peut pas être vide", "danger")
            return redirect(url_for('parametres_stock'))
        
        # Vérification de l'existence de la catégorie
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categorie WHERE id_categorie = %s", (id_categorie,))
        if not cur.fetchone():
            flash("La catégorie sélectionnée n'existe pas", "danger")
            return redirect(url_for('parametres_stock'))
        
        # Vérification de l'unicité du type dans la catégorie
        cur.execute("SELECT * FROM type WHERE nom_type = %s AND id_categorie = %s", 
                    (nom_type, id_categorie))
        if cur.fetchone():
            flash("Ce type existe déjà dans la catégorie sélectionnée", "warning")
            return redirect(url_for('parametres_stock'))
        
        # Insertion du nouveau type
        cur.execute("INSERT INTO type (nom_type, id_categorie) VALUES (%s, %s)", 
                    (nom_type, id_categorie))
        mysql.connection.commit()
        flash(f"Type '{nom_type}' créé avec succès", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la création du type : {str(e)}", "danger")
    finally:
        cur.close() if 'cur' in locals() else None
    
    return redirect(url_for('parametres_stock'))

@app.route('/editer_type/<int:id>', methods=['POST'])
def editer_type(id):
  
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    try:
        nom_type = request.form['nom_type'].strip()
        id_categorie = int(request.form['id_categorie'])
        
        if not nom_type:
            flash("Le nom du type ne peut pas être vide", "danger")
            return redirect(url_for('parametres_stock'))
        
        # Vérification de l'existence de la catégorie
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categorie WHERE id_categorie = %s", (id_categorie,))
        if not cur.fetchone():
            flash("La catégorie sélectionnée n'existe pas", "danger")
            return redirect(url_for('parametres_stock'))
        
        cur.execute("""
            SELECT * FROM type 
            WHERE nom_type = %s AND id_categorie = %s AND id_type != %s
        """, (nom_type, id_categorie, id))
        if cur.fetchone():
            flash("Ce nom de type est déjà utilisé dans cette catégorie", "warning")
            return redirect(url_for('parametres_stock'))
        
        # Mise à jour du type
        cur.execute("""
            UPDATE type 
            SET nom_type = %s, id_categorie = %s 
            WHERE id_type = %s
        """, (nom_type, id_categorie, id))
        mysql.connection.commit()
        flash(f"Type modifié avec succès", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la modification du type : {str(e)}", "danger")
    finally:
        cur.close() if 'cur' in locals() else None
    
    return redirect(url_for('parametres_stock'))

@app.route('/supprimer_type/<int:id>', methods=['POST'])
def supprimer_type(id):
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) as nb_articles FROM article WHERE id_type = %s", (id,))
        result = cur.fetchone()
        
        if result['nb_articles'] > 0:
            flash(f"Impossible de supprimer ce type : {result['nb_articles']} article(s) associé(s)", "danger")
            return redirect(url_for('parametres_stock'))
        
        # Suppression
        cur.execute("DELETE FROM type WHERE id_type = %s", (id,))
        mysql.connection.commit()
        flash("Type supprimé avec succès", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la suppression du type : {str(e)}", "danger")
    finally:
        cur.close() if 'cur' in locals() else None
    
    return redirect(url_for('parametres_stock'))

@app.route('/statistiques')
def statistiques():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT 
                l.id_laboratoire,
                l.nom_laboratoire,
                l.capacite,
                (SELECT COUNT(*) FROM tp WHERE id_laboratoire = l.id_laboratoire) AS nb_tp
            FROM laboratoire l
            ORDER BY l.nom_laboratoire
        """)
        labs_stats = cur.fetchall()

        # Données pour les graphiques
        lab_names = [lab['nom_laboratoire'] for lab in labs_stats]
        tp_counts = [lab['nb_tp'] for lab in labs_stats]
        capacities = [lab['capacite'] for lab in labs_stats]

        # Nouvelle requête avec type
        cur.execute("""
            SELECT 
                l.id_laboratoire,
                COALESCE(t.nom_type, 'Non spécifié') AS type_article,
                SUM(sl.quantite) as total_quantite
            FROM laboratoire l
            LEFT JOIN stock_laboratoire sl ON l.id_laboratoire = sl.id_laboratoire
            LEFT JOIN stock_magasin sm ON sl.id_lot = sm.id_lot
            LEFT JOIN article a ON sm.id_article = a.id_article
            LEFT JOIN type t ON a.id_type = t.id_type
            GROUP BY l.id_laboratoire, t.nom_type
        """)
        lab_types_data = cur.fetchall()
        types = sorted({lt['type_article'] for lt in lab_types_data if lt['type_article']}) 
        # Remplacer la boucle de traitement par :
        lab_types_dict = defaultdict(dict)
        for lt in lab_types_data:
            lab_id = lt['id_laboratoire']
            lab_types_dict[lab_id][lt['type_article']] = lt['total_quantite']
        # Création des paires catégorie/données
        type_data = []
        for type_name in types:
            counts = []
            for lab in labs_stats:
                counts.append(lab_types_dict[lab['id_laboratoire']].get(type_name, 0))
            type_data.append(counts)

        paired_data = list(zip(types, type_data))

        # Ajouter dans la partie statistiques
        cur.execute("""
            SELECT 
                DATE_FORMAT(heure_debut, '%x-W%v') AS semaine,
                COUNT(*) AS nb_tp
            FROM tp
            WHERE heure_debut >= NOW() - INTERVAL 1 YEAR
            GROUP BY semaine
            ORDER BY semaine
        """)
        timeline_data = cur.fetchall()
        timeline_dict = {item['semaine']: item['nb_tp'] for item in timeline_data}

        end_date = datetime.now()
        start_date = end_date - relativedelta(years=1)

        current_date = start_date
        weeks = []

        # Générer toutes les semaines ISO de la période
        while current_date <= end_date:
            iso_year, iso_week, _ = current_date.isocalendar()
            week_str = f"{iso_year}-W{iso_week:02d}"
            if not weeks or week_str != weeks[-1]:
                weeks.append(week_str)
            current_date += timedelta(days=7)

        # Formater les libellés et les données
        timeline_labels = []
        timeline_counts = []

        for week in weeks:
            year_part, week_part = week.split('-W')
            timeline_labels.append(f"Semaine {week_part}, {year_part}")
            timeline_counts.append(timeline_dict.get(week, 0))

        if not timeline_labels:  # Si pas de données
            timeline_labels = []
            timeline_counts = []


        return render_template('statistiques.html',
        lab_names=[lab['nom_laboratoire'] for lab in labs_stats],
        tp_counts=[lab['nb_tp'] for lab in labs_stats],
        types=types,
        type_data=type_data,
        timeline_labels=timeline_labels,
        timeline_data=timeline_counts,
        timeline_counts=timeline_counts )

    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close()

def nl2br(value):
    return value.replace('\n', '<br>') if value else ''

app.jinja_env.filters['nl2br'] = nl2br
@app.route('/recus/creer/<int:id_tp>', methods=['GET', 'POST'])
def creer_recu(id_tp):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        with mysql.connection.cursor() as cur:
            
            cur.execute("""
                SELECT r.id_recu 
                FROM recu r
                WHERE r.id_tp = %s
                LIMIT 1
            """, (id_tp,))
            existing_recu = cur.fetchone()

            if existing_recu:
                flash("Un reçu existe déjà pour ce TP", "warning")
                return redirect(url_for('detail_recu', id_recu=existing_recu['id_recu']))
            # Récupération TP
            cur.execute("""
                SELECT tp.*, l.nom_laboratoire, m.nom_matiere,
                    CONCAT(p.prenom, ' ', p.nom) AS professeur,
                    tp.id_prof, tp.id_laboratoire
                FROM tp tp
                JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
                JOIN matiere m ON tp.id_matiere = m.id_matiere
                JOIN professeur p ON tp.id_prof = p.id_prof
                WHERE tp.id_tp = %s
                FOR UPDATE
            """, (id_tp,))
            tp = cur.fetchone()

            if not tp:
                flash("TP introuvable", "danger")
                return redirect(url_for('index'))

            # Récupération articles disponibles
            cur.execute("""
                SELECT a.id_article, a.nom_article, a.unite_mesure,
                    SUM(sl.quantite) AS quantite_dispo
                FROM article a
                JOIN stock_magasin sm ON a.id_article = sm.id_article
                JOIN stock_laboratoire sl ON sm.id_lot = sl.id_lot
                WHERE sl.id_laboratoire = %s
                GROUP BY a.id_article
                HAVING quantite_dispo > 0
            """, (tp['id_laboratoire'],))
            articles = [dict(article) for article in cur.fetchall()]

            if request.method == 'POST':
                articles_data = []
                seen_articles = set()
                index = 0

                try:
                    # Extraction et validation des articles
                    while True:
                        article_key = f'articles[{index}][id]'
                        if article_key not in request.form:
                            break

                        article_id = int(request.form[article_key])
                        quantite = int(request.form.get(f'articles[{index}][quantite]', 0))
                        degrade = int(request.form.get(f'articles[{index}][degrade]', 0))

                        # Vérification des doublons
                        if article_id in seen_articles:
                            raise ValueError(f"Article {article_id} en double")
                        seen_articles.add(article_id)

                        # Vérification du stock
                        article_stock = next((a for a in articles if a['id_article'] == article_id), None)
                        if not article_stock:
                            raise ValueError(f"Article {article_id} invalide")

                        total = quantite + degrade
                        if total <= 0:
                            raise ValueError(f"Quantité totale nulle pour l'article {article_id}")
                        if total > article_stock['quantite_dispo']:
                            raise ValueError(f"Stock insuffisant pour {article_stock['nom_article']}")

                        articles_data.append({
                            'id_article': article_id,
                            'quantite': quantite,
                            'degrade': degrade
                        })
                        index += 1

                    if not articles_data:
                        flash("Aucun article sélectionné", "danger")
                        return redirect(url_for('creer_recu', id_tp=id_tp))

                    # Début transaction
                    with mysql.connection.cursor() as trans_cur:
                        # Création du reçu
                        # Modifier la partie d'insertion du reçu :
                        trans_cur.execute("""
                            INSERT INTO recu (id_tp, id_prof, date_emission, observations)
                            VALUES (%s, %s, NOW(), %s)
                        """, (id_tp, tp['id_prof'], request.form.get('observations', '')))
                        id_recu = trans_cur.lastrowid

                        # Insertion des lignes
                        for article in articles_data:
                            # Insertion ligne reçu
                            trans_cur.execute("""
                                INSERT INTO ligne_recu 
                                (id_recu, id_article, quantite, degradation_quantite)
                                VALUES (%s, %s, %s, %s)
                            """, (id_recu, article['id_article'], 
                                 article['quantite'], article['degrade']))

                            # Mise à jour stock avec verrou de ligne
                            trans_cur.execute("""
                                UPDATE stock_laboratoire sl
                                JOIN (
                                    SELECT id_lot 
                                    FROM stock_magasin
                                    WHERE id_article = %s
                                    ORDER BY date_expiration ASC
                                    LIMIT 1
                                    FOR UPDATE
                                ) sm ON sl.id_lot = sm.id_lot
                                SET sl.quantite = sl.quantite - %s
                                WHERE sl.id_laboratoire = %s
                            """, (article['id_article'], 
                                 article['degrade'], 
                                 tp['id_laboratoire']))

                        # Marquage TP comme traité
                        trans_cur.execute("""
                            UPDATE tp SET recu_genere = 1 
                            WHERE id_tp = %s
                        """, (id_tp,))

                        mysql.connection.commit()
                        flash("Reçu créé avec succès", "success")
                        return redirect(url_for('detail_recu', id_recu=id_recu))

                except ValueError as e:
                    mysql.connection.rollback()
                    flash(f"Erreur de validation : {str(e)}", "danger")

                except Exception as e:
                    mysql.connection.rollback()
                    flash(f"Erreur système : {str(e)}", "danger")

        return render_template('recus/creer.html', 
                            tp=tp, 
                            articles=articles)

    except Exception as e:
        flash(f"Erreur critique : {str(e)}", "danger")
        return redirect(url_for('index'))
    
@app.route('/recus')
def liste_recus():
    """Liste de tous les reçus"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT r.id_recu, r.date_emission, 
                   tp.nom_tp, l.nom_laboratoire,
                   CONCAT(p.prenom, ' ', p.nom) AS professeur
            FROM recu r
            JOIN tp tp ON r.id_tp = tp.id_tp
            JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
            JOIN professeur p ON r.id_prof = p.id_prof
            ORDER BY r.date_emission DESC
        """)
        recus = cur.fetchall()
        
        return render_template('recus/liste.html', recus=recus)
    
    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close()

@app.route('/recus/<int:id_recu>')
def detail_recu(id_recu):
    """Détail d'un reçu spécifique"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    try:
        # Récupération infos reçu
        cur.execute("""
            SELECT 
                r.*, 
                tp.nom_tp, 
                l.nom_laboratoire,
                m.nom_matiere,  -- Ajouter cette colonne
                CONCAT(p.prenom, ' ', p.nom) AS professeur
            FROM recu r
            JOIN tp tp ON r.id_tp = tp.id_tp
            JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
            JOIN matiere m ON tp.id_matiere = m.id_matiere  -- Nouvelle jointure
            JOIN professeur p ON r.id_prof = p.id_prof
            WHERE r.id_recu = %s
        """, (id_recu,))
        recu = cur.fetchone()
        
        if not recu:
            flash("Reçu introuvable", "danger")
            return redirect(url_for('liste_recus'))

        # Récupération articles
        cur.execute("""
            SELECT a.nom_article, lr.quantite, 
                   lr.degradation_quantite, a.unite_mesure
            FROM ligne_recu lr
            JOIN article a ON lr.id_article = a.id_article
            WHERE lr.id_recu = %s
        """, (id_recu,))
        articles = cur.fetchall()

        return render_template('recus/detail.html', 
                             recu=recu, 
                             articles=articles)
    
    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
        return redirect(url_for('liste_recus'))
    finally:
        cur.close()

@app.route('/recus/<int:id_recu>/supprimer', methods=['POST'])
def supprimer_recu(id_recu):
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT lr.id_article, lr.degradation_quantite, tp.id_laboratoire
            FROM ligne_recu lr
            JOIN recu r ON lr.id_recu = r.id_recu
            JOIN tp tp ON r.id_tp = tp.id_tp
            WHERE lr.id_recu = %s
        """, (id_recu,))
        degradations = cur.fetchall()

        with mysql.connection.cursor() as trans_cur:
            for d in degradations:
                # Étape 1 : Trouver le lot le plus ancien
                trans_cur.execute("""
                    SELECT sm.id_lot 
                    FROM stock_magasin sm
                    JOIN stock_laboratoire sl ON sm.id_lot = sl.id_lot
                    WHERE sm.id_article = %s
                    AND sl.id_laboratoire = %s
                    ORDER BY sm.date_expiration ASC 
                    LIMIT 1
                """, (d['id_article'], d['id_laboratoire']))
                lot = trans_cur.fetchone()

                if lot:
                    # Étape 2 : Mettre à jour le stock
                    trans_cur.execute("""
                        UPDATE stock_laboratoire
                        SET quantite = quantite + %s
                        WHERE id_lot = %s
                        AND id_laboratoire = %s
                    """, (d['degradation_quantite'], 
                         lot['id_lot'], 
                         d['id_laboratoire']))

            # Suppression du reçu
            trans_cur.execute("DELETE FROM recu WHERE id_recu = %s", (id_recu,))
            trans_cur.execute("UPDATE tp SET recu_genere = 0 WHERE id_tp = (SELECT id_tp FROM recu WHERE id_recu = %s)", (id_recu,))

            mysql.connection.commit()
            flash("Reçu supprimé avec succès", "success")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "danger")
    finally:
        cur.close()
    
    return redirect(url_for('liste_recus'))

@app.route('/recus/<int:id_recu>/imprimer')
def imprimer_recu(id_recu):
    """Version imprimable d'un reçu"""
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
        SELECT 
            r.*, 
            tp.nom_tp, 
            l.nom_laboratoire,
            m.nom_matiere,  -- À ajouter
            CONCAT(p.prenom, ' ', p.nom) AS professeur
        FROM recu r
        JOIN tp tp ON r.id_tp = tp.id_tp
        JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
        JOIN matiere m ON tp.id_matiere = m.id_matiere  -- Jointure manquante
        JOIN professeur p ON r.id_prof = p.id_prof
        WHERE r.id_recu = %s
    """, (id_recu,))
        recu = cur.fetchone()
        
        cur.execute("""
            SELECT a.nom_article, lr.quantite, 
                   lr.degradation_quantite, a.unite_mesure
            FROM ligne_recu lr
            JOIN article a ON lr.id_article = a.id_article
            WHERE lr.id_recu = %s
        """, (id_recu,))
        articles = cur.fetchall()

        return render_template('recus/imprimer.html',
                             recu=recu,
                             articles=articles)

    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for('liste_recus'))
    finally:
        cur.close()

@app.route('/recus/<int:id_recu>/editer', methods=['GET', 'POST'])
def editer_recu(id_recu):
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)

    try:
        with mysql.connection.cursor() as cur:
            # Récupération des données existantes
            cur.execute("""
                SELECT 
                    r.*,
                    tp.id_tp,
                    tp.nom_tp,
                    tp.heure_debut,
                    tp.id_laboratoire,
                    l.nom_laboratoire,
                    m.nom_matiere,
                    tp.id_prof,
                    CONCAT(p.prenom, ' ', p.nom) AS professeur
                FROM recu r
                JOIN tp ON r.id_tp = tp.id_tp
                JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
                JOIN matiere m ON tp.id_matiere = m.id_matiere
                JOIN professeur p ON tp.id_prof = p.id_prof
                WHERE r.id_recu = %s
                FOR UPDATE
            """, (id_recu,))
            recu = cur.fetchone()

            if not recu:
                flash("Reçu introuvable", "danger")
                return redirect(url_for('liste_recus'))
            
            # Récupération des articles existants
            cur.execute("""
                SELECT 
                    a.id_article,
                    a.nom_article,
                    lr.quantite,
                    lr.degradation_quantite,
                    a.unite_mesure
                FROM ligne_recu lr
                JOIN article a ON lr.id_article = a.id_article
                WHERE lr.id_recu = %s
            """, (id_recu,))
            existing_articles = cur.fetchall()

            # Récupération du stock actuel
            cur.execute("""
                SELECT 
                    a.id_article,
                    SUM(sl.quantite) AS stock_dispo
                FROM stock_laboratoire sl
                JOIN stock_magasin sm ON sl.id_lot = sm.id_lot
                JOIN article a ON sm.id_article = a.id_article
                WHERE sl.id_laboratoire = %s
                GROUP BY a.id_article
            """, (recu['id_laboratoire'],))
            stock_data = {row['id_article']: row['stock_dispo'] for row in cur.fetchall()}

            # Calcul du stock ajusté
            adjusted_stock = stock_data.copy()
            for article in existing_articles:
                adjusted_stock[article['id_article']] += article['degradation_quantite']

            if request.method == 'POST':
                try:
                    observations = request.form.get('observations', '')
                    articles_data = []
                    seen_articles = set()
                    index = 0

                    # Extraction et validation
                    while True:
                        id_key = f'articles[{index}][id]'
                        if id_key not in request.form:
                            break
                        
                        article_id = int(request.form[id_key])
                        quantite = int(request.form.get(f'articles[{index}][quantite]', 0))
                        degrade = int(request.form.get(f'articles[{index}][degrade]', 0))

                        # Validation
                        if article_id in seen_articles:
                            raise ValueError(f"Article {article_id} en double")
                        seen_articles.add(article_id)

                        if degrade > adjusted_stock.get(article_id, 0):
                            raise ValueError(f"Dégradations trop importantes pour l'article {article_id}. Disponible: {adjusted_stock.get(article_id)}, Demandé: {degrade}")

                        articles_data.append({
                            'id': article_id,
                            'quantite': quantite,
                            'degrade': degrade
                        })
                        index += 1

                    # Début transaction
                    with mysql.connection.cursor() as trans_cursor:
                        # Restauration stock original (dégradations seulement)
                        for article in existing_articles:
                            trans_cursor.execute("""
                                UPDATE stock_laboratoire sl
                                JOIN (
                                    SELECT id_lot 
                                    FROM stock_magasin 
                                    WHERE id_article = %s 
                                    ORDER BY date_expiration ASC 
                                    LIMIT 1
                                ) sm ON sl.id_lot = sm.id_lot
                                SET sl.quantite = sl.quantite + %s
                                WHERE sl.id_laboratoire = %s
                            """, (article['id_article'], article['degradation_quantite'], recu['id_laboratoire']))

                        # Suppression anciennes lignes
                        trans_cursor.execute("DELETE FROM ligne_recu WHERE id_recu = %s", (id_recu,))

                        # Insertion nouvelles lignes
                        for article in articles_data:
                            trans_cursor.execute("""
                                INSERT INTO ligne_recu 
                                (id_recu, id_article, quantite, degradation_quantite)
                                VALUES (%s, %s, %s, %s)
                            """, (id_recu, article['id'], article['quantite'], article['degrade']))

                            # Mise à jour stock (dégradations seulement)
                            trans_cursor.execute("""
                                UPDATE stock_laboratoire sl
                                JOIN (
                                    SELECT id_lot 
                                    FROM stock_magasin 
                                    WHERE id_article = %s 
                                    ORDER BY date_expiration ASC 
                                    LIMIT 1
                                ) sm ON sl.id_lot = sm.id_lot
                                SET sl.quantite = sl.quantite - %s
                                WHERE sl.id_laboratoire = %s
                            """, (article['id'], article['degrade'], recu['id_laboratoire']))

                        # Mise à jour observations
                        trans_cursor.execute("""
                            UPDATE recu 
                            SET observations = %s 
                            WHERE id_recu = %s
                        """, (observations, id_recu))

                        mysql.connection.commit()
                        flash("Reçu mis à jour avec succès", "success")
                        return redirect(url_for('detail_recu', id_recu=id_recu))

                except Exception as e:
                    mysql.connection.rollback()
                    flash(f"Erreur de mise à jour : {str(e)}", "danger")

            # Récupération articles disponibles
            cur.execute("""
                SELECT 
                    a.id_article, 
                    a.nom_article, 
                    a.unite_mesure,
                    SUM(sl.quantite) AS quantite_dispo
                FROM article a
                JOIN stock_magasin sm ON a.id_article = sm.id_article
                JOIN stock_laboratoire sl ON sm.id_lot = sl.id_lot
                WHERE sl.id_laboratoire = %s
                GROUP BY a.id_article
                HAVING quantite_dispo > 0
            """, (recu['id_laboratoire'],))
            available_articles = cur.fetchall()

            return render_template('recus/editer.html',
                                recu=recu,
                                existing_articles=existing_articles,
                                available_articles=available_articles,
                                stock=adjusted_stock)

    except Exception as e:
        flash(f"Erreur critique : {str(e)}", "danger")
        return redirect(url_for('liste_recus'))


def is_valid_password(password):
    return len(password) >= 4 and any(c.isalpha() for c in password)
# CRUD Utilisateurs (Admins)
@app.route('/admin/utilisateurs')
def liste_utilisateurs():
    if ('user_id' not in session or session.get('role') not in ['admin', 'super_admin']):
        abort(403)
    
    cur = mysql.connection.cursor()
    try:
        # Exemple dans liste_utilisateurs
        cur.execute("""
        SELECT id, username, email, role, is_active 
        FROM utilisateur 
        ORDER BY username
    """)
        utilisateurs = cur.fetchall()
        return render_template('admin/utilisateurs/liste.html', utilisateurs=utilisateurs)
    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close()

@app.route('/admin/utilisateurs/creer', methods=['GET', 'POST'])
def creer_utilisateur():
    if 'user_id' not in session or session.get('role') != ('admin' or 'super_admin'):
        abort(403)
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        role = request.form.get('role', 'user')
        
        if not all([username, email, password]):
            flash("Tous les champs obligatoires doivent être remplis", "danger")
            return redirect(url_for('creer_utilisateur'))
        
        if not is_valid_password(password):
            flash("Le mot de passe doit contenir au moins 4 caractères et une lettre", "danger")
            return redirect(url_for('creer_utilisateur'))
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT id FROM utilisateur WHERE username = %s OR email = %s", (username, email))
            if cur.fetchone():
                flash("Nom d'utilisateur ou email déjà utilisé", "danger")
                return redirect(url_for('creer_utilisateur'))
            
            hashed_pw = generate_password_hash(password)
            cur.execute("""
                INSERT INTO utilisateur (username, email, password, role)
                VALUES (%s, %s, %s, %s)
            """, (username, email, hashed_pw, role))
            mysql.connection.commit()
            flash("Utilisateur créé avec succès", "success")
            return redirect(url_for('liste_utilisateurs'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur : {str(e)}", "danger")
        finally:
            cur.close()
    
    return render_template('admin/utilisateurs/creer.html')


@app.route('/admin/utilisateurs/editer/<int:id>', methods=['GET', 'POST'])
def editer_utilisateur(id):
    # Vérification des permissions
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        abort(403)
    
    is_super_admin = (session.get('role') == 'super_admin')
    cur = mysql.connection.cursor()
    
    try:
        if request.method == 'POST':
            # Récupération des données du formulaire
            username = request.form['username'].strip()
            email = request.form['email'].strip()
            role = request.form.get('role', 'user')
            new_password = request.form.get('new_password', '').strip()

            # Vérification des champs obligatoires
            if not all([username, email]):
                flash("Les champs obligatoires doivent être remplis", "danger")
                return redirect(url_for('editer_utilisateur', id=id))

            # Validation du mot de passe
            if new_password and not is_valid_password(new_password):
                flash("Le mot de passe doit contenir au moins 4 caractères et une lettre", "danger")
                return redirect(url_for('editer_utilisateur', id=id))

            # Vérification des doublons
            cur.execute("SELECT id FROM utilisateur WHERE (username = %s OR email = %s) AND id != %s", 
                       (username, email, id))
            if cur.fetchone():
                flash("Nom d'utilisateur ou email déjà utilisé", "danger")
                return redirect(url_for('editer_utilisateur', id=id))

            # Protection contre la modification des super_admins
            cur.execute("SELECT role FROM utilisateur WHERE id = %s", (id,))
            old_role = cur.fetchone()['role']

            # Seul un super_admin peut modifier un super_admin
            if old_role == 'super_admin' and not is_super_admin:
                flash("Action non autorisée", "danger")
                return redirect(url_for('liste_utilisateurs'))

            # Empêcher la suppression du dernier super_admin
            if old_role == 'super_admin' and role != 'super_admin':
                cur.execute("SELECT COUNT(*) as count FROM utilisateur WHERE role = 'super_admin' AND id != %s", (id,))
                if cur.fetchone()['count'] == 0:
                    flash("Il doit rester au moins un super admin", "danger")
                    return redirect(url_for('editer_utilisateur', id=id))

            # Mise à jour de la base de données
            update_fields = ["username = %s", "email = %s", "role = %s"]
            params = [username, email, role]

            if new_password:
                hashed_pw = generate_password_hash(new_password)
                update_fields.append("password = %s")
                params.append(hashed_pw)

            params.append(id)
            query = "UPDATE utilisateur SET " + ", ".join(update_fields) + " WHERE id = %s"
            cur.execute(query, tuple(params))
            mysql.connection.commit()

            flash("Modifications enregistrées avec succès", "success")
            return redirect(url_for('liste_utilisateurs'))

        # Récupération des données utilisateur
        cur.execute("SELECT id, username, email, role, is_active FROM utilisateur WHERE id = %s", (id,))
        utilisateur = cur.fetchone()

        if not utilisateur:
            flash("Utilisateur introuvable", "danger")
            return redirect(url_for('liste_utilisateurs'))

        return render_template('admin/utilisateurs/editer.html',
                             utilisateur=utilisateur,
                             is_super_admin=is_super_admin)

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la mise à jour : {str(e)}", "danger")
        return redirect(url_for('liste_utilisateurs'))
    
    finally:
        cur.close()

# Modification de la route de suppression
@app.route('/admin/utilisateurs/supprimer/<int:id>', methods=['POST'])
def supprimer_utilisateur(id):
    if ('user_id' not in session or session.get('role') != 'super_admin'):  # Seul super_admin
        abort(403)
    
    if session.get('user_id') == id:
        flash("Vous ne pouvez pas supprimer votre propre compte", "danger")
        return redirect(url_for('liste_utilisateurs'))
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM utilisateur WHERE id = %s", (id,))
        mysql.connection.commit()
        flash("Utilisateur supprimé définitivement", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur : {str(e)}", "danger")
    finally:
        cur.close()
    return redirect(url_for('liste_utilisateurs'))

# Nouvelle route pour activer/désactiver
@app.route('/admin/utilisateurs/toggle-active/<int:id>', methods=['POST'])
def toggle_active_user(id):
    if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
        abort(403)
    
    current_user_id = session['user_id']
    
    if id == current_user_id:
        flash("Vous ne pouvez pas modifier votre propre statut", "danger")
        return redirect(url_for('liste_utilisateurs'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Vérification supplémentaire de l'existence de l'utilisateur
        cur.execute("SELECT id FROM utilisateur WHERE id = %s", (id,))
        if not cur.fetchone():
            flash("Utilisateur introuvable", "danger")
            return redirect(url_for('liste_utilisateurs'))
        
        # Mise à jour du statut
        cur.execute("UPDATE utilisateur SET is_active = NOT is_active WHERE id = %s", (id,))
        mysql.connection.commit()
        
        # Récupération du nouveau statut
        cur.execute("SELECT is_active FROM utilisateur WHERE id = %s", (id,))
        new_status = cur.fetchone()['is_active']
        
        flash(f"Statut modifié : {'Activé' if new_status else 'Désactivé'}", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur de base de données : {str(e)}", "danger")
    finally:
        cur.close()
    
    return redirect(url_for('liste_utilisateurs'))


# Route profil utilisateur
@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("SELECT * FROM utilisateur WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if request.method == 'POST':
            current_password = request.form.get('current_password', '').strip()
            new_username = request.form.get('username', '').strip()
            new_email = request.form.get('email', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            cur.execute("SELECT * FROM utilisateur WHERE id = %s", (user_id,))
            user = cur.fetchone()
            
            updates = []
            params = []
            
            if new_username and new_username != user['username']:
                cur.execute("SELECT id FROM utilisateur WHERE username = %s", (new_username,))
                if cur.fetchone():
                    flash("Ce nom d'utilisateur est déjà pris", "danger")
                else:
                    updates.append("username = %s")
                    params.append(new_username)

            # Vérification email
            if new_email and new_email != user['email']:
                cur.execute("SELECT id FROM utilisateur WHERE email = %s AND id != %s", 
                           (new_email, user_id))
                if cur.fetchone():
                    flash("Cet email est déjà utilisé", "danger")
                else:
                    updates.append("email = %s")
                    params.append(new_email)
                    session['email'] = new_email
            
            # Vérification mot de passe
            if new_password:
                if not check_password_hash(user['password'], current_password):
                    flash("Mot de passe actuel incorrect", "danger")
                elif new_password != confirm_password:
                    flash("Les mots de passe ne correspondent pas", "danger")
                elif not is_valid_password(new_password):
                    flash("Le mot de passe doit contenir au moins 4 caractères et une lettre", "danger")
                else:
                    hashed_pw = generate_password_hash(new_password)
                    updates.append("password = %s")
                    params.append(hashed_pw)
            
            if updates:
                params.append(user_id)
                query = "UPDATE utilisateur SET " + ", ".join(updates) + " WHERE id = %s"
                cur.execute(query, tuple(params))
                mysql.connection.commit()
                flash("Profil mis à jour avec succès", "success")
            
            return redirect(url_for('profil'))
        
        cur.execute("SELECT id, username, email, role FROM utilisateur WHERE id = %s", (user_id,))
        user = cur.fetchone()
        return render_template('profil.html', user=user)

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur lors de la mise à jour : {str(e)}", "danger")
        return redirect(url_for('profil'))
    finally:
        cur.close()


def send_password_reset_email(user_email, code):
    try:
        msg = Message(
            "Réinitialisation de mot de passe - LabManager",
            recipients=[user_email],
            html=render_template('emails/reset_password.html', code=code)
        )
        
        # Debug SMTP
        with app.app_context():
            mail.connect()
            app.logger.info(f"Connexion SMTP établie à {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
            mail.send(msg)
            app.logger.info(f"Email envoyé à {user_email} via {app.config['MAIL_USERNAME']}")

    except smtplib.SMTPException as e:
        app.logger.error(f"Erreur SMTP (code {e.smtp_code}): {e.smtp_error.decode()}")
        raise
    except Exception as e:
        app.logger.error(f"Erreur générale: {str(e)}", exc_info=True)
        raise


# Initialiser le sérialiseur
ts = URLSafeTimedSerializer(app.secret_key)

def generate_verification_code(length=6):
    return ''.join(secrets.choice('0123456789') for _ in range(length))

# Route forgot_password corrigée
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, email FROM utilisateur WHERE email = %s", (email,))
            user = cur.fetchone()
            
            if not user:
                flash("Aucun compte associé à cet email", "warning")
                return redirect(url_for('forgot_password'))

            # Generate verification code
            code = generate_verification_code()
            
            # Store code, email, and expiration time in session
            session['reset_code'] = code
            session['reset_email'] = email
            session['reset_expires'] = datetime.now().timestamp() + 900  # 15 minutes
            
            # Send the code via email
            send_password_reset_email(email, code)
            
            flash("Un code de vérification a été envoyé à votre adresse email.", "success")
            return redirect(url_for('verify_code'))
            
        except Exception as e:
            app.logger.error(f"Erreur : {str(e)}")
            flash("Erreur lors de l'envoi du code de réinitialisation", "danger")
        finally:
            cur.close()

    return render_template('forgot_password.html')


@app.route('/verify-code', methods=['GET', 'POST'])
def verify_code():
    # Vérifier la présence du code en session
    reset_code = session.get('reset_code')
    reset_email = session.get('reset_email')
    expires = session.get('reset_expires', 0)
    
    if not reset_code or not reset_email or datetime.now().timestamp() > expires:
        flash("Le code a expiré ou est invalide", "danger")
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        entered_code = request.form.get('code', '').strip()
        
        if entered_code == reset_code:
            session['code_verified'] = True
            return redirect(url_for('reset_password'))
        else:
            flash("Code incorrect", "danger")
    
    # Fichier template: templates/verify_code.html
    return render_template('verify_code.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    # Vérifier si l'utilisateur a validé le code
    if not session.get('code_verified') or not session.get('reset_email'):
        flash("Veuillez d'abord vérifier votre code", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password'].strip()
        confirm_password = request.form['confirm_password'].strip()

        # Validation des mots de passe
        if not new_password or not confirm_password:
            flash("Veuillez remplir tous les champs", "danger")
            return redirect(url_for('reset_password'))
        
        if new_password != confirm_password:
            flash("Les mots de passe ne correspondent pas", "danger")
            return redirect(url_for('reset_password'))
        
        if not is_valid_password(new_password):
            flash("Le mot de passe doit contenir au moins 4 caractères avec une lettre", "danger")
            return redirect(url_for('reset_password'))

        # Mise à jour du mot de passe
        try:
            cur = mysql.connection.cursor()
            hashed_pw = generate_password_hash(new_password)
            cur.execute(
                "UPDATE utilisateur SET password = %s WHERE email = %s",
                (hashed_pw, session['reset_email'])
            )
            mysql.connection.commit()

            # Nettoyage de la session
            session.pop('reset_code', None)
            session.pop('reset_email', None)
            session.pop('reset_expires', None)
            session.pop('code_verified', None)

            flash("Mot de passe mis à jour avec succès ! Vous pouvez maintenant vous connecter", "success")
            return redirect(url_for('login'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur lors de la mise à jour : {str(e)}", "danger")
        finally:
            cur.close()

    return render_template('reset_password.html')

# Fichier de stockage des codes (hors de la base de données)
ACCESS_CODE_FILE = 'access_codes.json'

def generate_access_code():
    """Génère un code d'accès sécurisé"""
    return secrets.token_hex(3).upper()  # Exemple: 'A3B9F2'

def save_access_code(email, code):
    data = {}
    if os.path.exists(ACCESS_CODE_FILE):
        with open(ACCESS_CODE_FILE, 'r') as f:
            data = json.load(f)
    
    data[email] = {
        'code': code,
        'expires': time.time() + 600  # 10 minutes en secondes
    }
    
    with open(ACCESS_CODE_FILE, 'w') as f:
        json.dump(data, f)

def get_access_code(email):
    if not os.path.exists(ACCESS_CODE_FILE):
        return None
    
    with open(ACCESS_CODE_FILE, 'r') as f:
        data = json.load(f)
    
    entry = data.get(email)
    # Vérification du timestamp avec time.time()
    if entry and entry['expires'] > time.time():
        return entry['code']
    
    return None

@app.route('/admin/request-code', methods=['GET', 'POST'])
def request_admin_code():
    if ('user_id' not in session or session.get('role') not in ['super_admin']):
        abort(403)
    
    admin_email = session['email']
    
    if request.method == 'POST':
        # Générer et envoyer un nouveau code
        new_code = generate_access_code()
        save_access_code(admin_email, new_code)
        
        # Envoyer le code par email
        msg = Message("Votre code d'accès administrateur",
                      recipients=[admin_email])
        msg.body = f"Votre code d'accès temporaire est : {new_code}"
        mail.send(msg)
        
        flash("Un nouveau code a été envoyé à votre adresse email", "success")
        return redirect(url_for('verify_admin_access'))
    
    return render_template('admin/request_code.html')

@app.route('/admin/verify', methods=['GET', 'POST'])
def verify_admin_access():
    if ('user_id' not in session or session.get('role') not in ['super_admin']):
        abort(403)
    
    admin_email = session['email']
    saved_code = get_access_code(admin_email)

    # Génération automatique du code si absent/expiré (méthode GET)
    if request.method == 'GET':
        if not saved_code:
            new_code = generate_access_code()
            save_access_code(admin_email, new_code)
            
            msg = Message("Votre code d'accès administrateur",
                        recipients=[admin_email])
            msg.body = f"Votre code d'accès temporaire est : {new_code}"
            mail.send(msg)
            
            flash("Un nouveau code a été envoyé à votre adresse email", "success")

    # Traitement de la soumission du formulaire (méthode POST)
    if request.method == 'POST':
        entered_code = request.form.get('code', '').strip().upper()
        
        if not entered_code:
            flash("Veuillez entrer un code de vérification", "danger")
            return redirect(url_for('verify_admin_access'))
            
        if len(entered_code) != 6:
            flash("Le code doit contenir exactement 6 caractères", "danger")
            return redirect(url_for('verify_admin_access'))

        saved_code = get_access_code(admin_email)  # Re-vérification après possible génération en GET
        if saved_code and entered_code == saved_code:
            session['admin_verified'] = True
            return redirect(url_for('parametres'))
        else:
            flash("Code invalide ou expiré", "danger")
    
    return render_template('admin/verify.html')

@app.route('/parametres', methods=['GET', 'POST'])
def parametres():

    if not session.get('admin_verified'):
       return redirect(url_for('verify_admin_access'))
    # Récupération des données
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM laboratoire")
        laboratoires = cur.fetchall()
        cur.execute("SELECT * FROM matiere")
        matieres = cur.fetchall()
        cur.execute("SELECT * FROM professeur")
        professeurs = cur.fetchall()
    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", 'danger')
        return redirect(url_for('index'))
    finally:
        cur.close()

    if request.method == 'POST':
        action = request.form.get('action')
        cur = mysql.connection.cursor()
        
        try:
            if action == 'delete_labs':
                selected_labs = request.form.get('selected_labs', '').split(',')
                if not selected_labs or selected_labs[0] == '':
                    flash("Aucun laboratoire sélectionné", 'warning')
                    return redirect(url_for('parametres'))

                mysql.connection.begin()
                for lab_id in selected_labs:
                    # Transfert correct du stock
                    cur.execute("""
                        UPDATE stock_magasin sm
                        JOIN stock_laboratoire sl ON sm.id_lot = sl.id_lot
                        SET sm.quantite = sm.quantite + sl.quantite
                        WHERE sl.id_laboratoire = %s
                    """, (lab_id,))
                    
                    # Suppression des données associées
                    cur.execute("""
                        DELETE FROM ligne_recu
                        WHERE id_recu IN (
                            SELECT id_recu FROM recu
                            WHERE id_tp IN (
                                SELECT id_tp FROM tp WHERE id_laboratoire = %s
                            )
                        )
                    """, (lab_id,))
                    cur.execute("DELETE FROM recu WHERE id_tp IN (SELECT id_tp FROM tp WHERE id_laboratoire = %s)", (lab_id,))
                    cur.execute("DELETE FROM tp WHERE id_laboratoire = %s", (lab_id,))
                    cur.execute("DELETE FROM stock_laboratoire WHERE id_laboratoire = %s", (lab_id,))
                    cur.execute("DELETE FROM laboratoire WHERE id_laboratoire = %s", (lab_id,))
                
                mysql.connection.commit()
                flash(f"{len(selected_labs)} laboratoire(s) supprimés", 'success')

            elif action == 'transfer_stock':
                selected_labs = request.form.get('selected_labs', '').split(',')
                if not selected_labs or selected_labs[0] == '':
                    flash("Aucun laboratoire sélectionné", 'warning')
                    return redirect(url_for('parametres'))

                mysql.connection.begin()
                for lab_id in selected_labs:
                    # Transfert sécurisé sans date_expiration
                    cur.execute("""
                        UPDATE stock_magasin sm
                        JOIN stock_laboratoire sl ON sm.id_lot = sl.id_lot
                        SET sm.quantite = sm.quantite + sl.quantite
                        WHERE sl.id_laboratoire = %s
                    """, (lab_id,))
                    cur.execute("DELETE FROM stock_laboratoire WHERE id_laboratoire = %s", (lab_id,))
                
                mysql.connection.commit()
                flash("Stock transféré avec succès", 'success')

            elif action == 'clear_lab_stock':
                selected_labs = request.form.get('selected_labs', '').split(',')
                placeholders = ','.join(['%s'] * len(selected_labs))
                cur.execute(f"DELETE FROM stock_laboratoire WHERE id_laboratoire IN ({placeholders})", selected_labs)
                mysql.connection.commit()
                flash("Stock laboratoire(s) vidé", 'success')

            elif action == 'delete_filtered_tp':
                filters = json.loads(request.form.get('filters', '{}'))
                
                conditions = []
                params = []
                if filters.get('start'):
                    conditions.append("heure_debut >= %s")
                    params.append(filters['start'])
                if filters.get('end'):
                    conditions.append("heure_fin <= %s")
                    params.append(filters['end'])
                if filters.get('lab'):
                    conditions.append("id_laboratoire = %s")
                    params.append(filters['lab'])
                if filters.get('matiere'):
                    conditions.append("id_matiere = %s")
                    params.append(filters['matiere'])
                if filters.get('prof'):
                    conditions.append("id_prof = %s")
                    params.append(filters['prof'])
                
                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

                mysql.connection.begin()
                # Suppression en cascade sécurisée
                cur.execute(f"""
                    DELETE FROM ligne_recu
                    WHERE id_recu IN (
                        SELECT id_recu FROM recu
                        WHERE id_tp IN (
                            SELECT id_tp FROM tp {where_clause}
                        )
                    )
                """, params)
                cur.execute(f"DELETE FROM recu WHERE id_tp IN (SELECT id_tp FROM tp {where_clause})", params)
                cur.execute(f"DELETE FROM tp {where_clause}", params)
                mysql.connection.commit()
                flash("TPs filtrés supprimés", 'success')

            elif action == 'delete_all_tp':
                mysql.connection.begin()
                cur.execute("DELETE FROM ligne_recu")
                cur.execute("DELETE FROM recu")
                cur.execute("DELETE FROM tp")
                mysql.connection.commit()
                flash("Tous les TPs supprimés", 'success')

            elif action == 'clear_store_stock':
                cur.execute("UPDATE stock_magasin SET quantite = 0")
                mysql.connection.commit()
                flash("Stock magasin réinitialisé", 'success')

            elif action == 'delete_all_profs':
                mysql.connection.begin()
                cur.execute("""
                    DELETE FROM ligne_recu
                    WHERE id_recu IN (
                        SELECT id_recu FROM recu
                        WHERE id_tp IN (
                            SELECT id_tp FROM tp WHERE id_prof IS NOT NULL
                        )
                    )
                """)
                cur.execute("DELETE FROM recu WHERE id_tp IN (SELECT id_tp FROM tp WHERE id_prof IS NOT NULL)")
                cur.execute("DELETE FROM tp WHERE id_prof IS NOT NULL")
                cur.execute("DELETE FROM professeur")
                mysql.connection.commit()
                flash("Tous les professeurs supprimés", 'success')

            elif action == 'delete_all_matieres':
                mysql.connection.begin()
                cur.execute("""
                    DELETE FROM ligne_recu
                    WHERE id_recu IN (
                        SELECT id_recu FROM recu
                        WHERE id_tp IN (
                            SELECT id_tp FROM tp WHERE id_matiere IS NOT NULL
                        )
                    )
                """)
                cur.execute("DELETE FROM recu WHERE id_tp IN (SELECT id_tp FROM tp WHERE id_matiere IS NOT NULL)")
                cur.execute("DELETE FROM tp WHERE id_matiere IS NOT NULL")
                cur.execute("DELETE FROM matiere")
                mysql.connection.commit()
                flash("Toutes les matières supprimées", 'success')

        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur : {str(e)}", 'danger')
        finally:
            cur.close()

        return redirect(url_for('parametres'))

    return render_template('parametres.html',
                         laboratoires=laboratoires,
                         matieres=matieres,
                         professeurs=professeurs)

@app.route('/sds/<filename>')
def view_sds(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



if __name__ == '__main__':
    # Création des utilisateurs dans un contexte d'application
    with app.app_context():
        create_default_users()
    
    # Lancer le serveur en mode debug accessible sur le réseau
    app.run(host='0.0.0.0', port=5000, debug=True)
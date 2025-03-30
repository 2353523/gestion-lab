import os
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort,render_template_string,Response  
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from flask_session import Session 
from flask_wtf.csrf import CSRFProtect
import mysql.connector
import locale
from collections import defaultdict





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
    
    return redirect(url_for('index', week_offset=redirect_week))

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
        if request.method == 'HEAD':
            return Response()
        locale.setlocale(locale.LC_TIME, 'french')  # Alternative pour Windows

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
    if 'user_id' not in session or session['role'] != 'admin':
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
                c.nom_categorie
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

    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
    finally:
        if cur:
            cur.close()

    return render_template('stock/stock_magasin.html',
                         stock=stock,
                         categories=categories,
                         types=types)


# Route pour ajouter un article
@app.route('/ajouter_article', methods=['GET', 'POST'])
def ajouter_article():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()

        if request.method == 'POST':
            nom = request.form['nom']
            unite = request.form['unite']
            quantite = int(request.form['quantite'])
            id_type = int(request.form['type'])
            date_expiration = request.form.get('date_expiration') or None

            try:
                with mysql.connection.cursor() as trans_cur:
                    # Création de l'article
                    trans_cur.execute("""
                        INSERT INTO article (nom_article, unite_mesure, id_type, date_expiration)
                        VALUES (%s, %s, %s, %s)
                    """, (nom, unite, id_type, date_expiration))
                    id_article = trans_cur.lastrowid

                    # Création du lot
                    trans_cur.execute("""
                        INSERT INTO stock_magasin (id_article, quantite, date_expiration)
                        VALUES (%s, %s, %s)
                    """, (id_article, quantite, date_expiration))

                    mysql.connection.commit()
                    flash("Article et lot créés avec succès", "success")
                    return redirect(url_for('stock_magasin'))

            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur : {str(e)}", "danger")

        return render_template('stock/ajouter_article.html',
                             categories=categories,
                             types=types)

    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for('stock_magasin'))
    finally:
        cur.close()

# Route pour éditer un article
@app.route('/editer_article/<int:id>', methods=['GET', 'POST'])
def editer_article(id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            # Récupération des données
            nom = request.form['nom']
            unite = request.form['unite']
            quantite = int(request.form['quantite'])
            id_type = int(request.form['type'])
            date_expiration = request.form.get('date_expiration') or None

            with mysql.connection.cursor() as trans_cur:
                # Mise à jour article avec date d'expiration
                trans_cur.execute("""
                    UPDATE article SET
                        nom_article = %s,
                        unite_mesure = %s,
                        id_type = %s,
                        date_expiration = %s
                    WHERE id_article = %s
                """, (nom, unite, id_type, date_expiration, id))

                # Mise à jour stock magasin avec date d'expiration
                trans_cur.execute("""
                    UPDATE stock_magasin SET
                        quantite = %s,
                        date_expiration = %s
                    WHERE id_article = %s
                    ORDER BY date_expiration ASC
                    LIMIT 1
                """, (quantite, date_expiration, id))

                mysql.connection.commit()
                flash("Modifications enregistrées", "success")
                return redirect(url_for('stock_magasin'))

        # Récupération données existantes avec jointure
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
            ORDER BY sm.date_expiration ASC
            LIMIT 1
        """, (id,))
        article = cur.fetchone()

        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()

        return render_template('stock/editer_article.html',
                             article=article,
                             categories=categories,
                             types=types)

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for('stock_magasin'))
    finally:
        cur.close()

@app.route('/supprimer_article/<int:id>', methods=['POST'])
def supprimer_article(id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))

    try:
        with mysql.connection.cursor() as trans_cur:
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
                t.id_categorie
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
    """
    Affiche l'interface de gestion des catégories et types d'articles.
    Interface destinée uniquement aux administrateurs.
    
    Cette route récupère depuis la base de données:
    - La liste complète des catégories
    - La liste complète des types avec leurs catégories associées
    pour permettre leur visualisation et gestion.
    
    Returns:
        Response: Rendu du template de gestion des paramètres ou redirection
    """
    if 'user_id' not in session or session['role'] != 'admin':
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
    """
    Traite l'ajout d'une nouvelle catégorie d'articles.
    Accessible uniquement aux administrateurs via méthode POST.
    
    Vérifie l'unicité du nom de catégorie avant insertion
    pour éviter les doublons.
    
    Returns:
        Response: Redirection avec message de confirmation ou d'erreur
    """
    if 'user_id' not in session or session['role'] != 'admin':
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
    """
    Met à jour une catégorie existante identifiée par son ID.
    Accessible uniquement aux administrateurs via méthode POST.
    
    Args:
        id (int): Identifiant de la catégorie à modifier
    
    Vérifie l'existence de la catégorie et l'unicité du nouveau nom
    avant d'effectuer la mise à jour.
    
    Returns:
        Response: Redirection avec message de confirmation ou d'erreur
    """
    if 'user_id' not in session or session['role'] != 'admin':
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
    """
    Supprime une catégorie identifiée par son ID.
    Accessible uniquement aux administrateurs via méthode POST.
    
    Args:
        id (int): Identifiant de la catégorie à supprimer
    
    Vérifie l'absence de types associés avant de procéder à la suppression
    pour maintenir l'intégrité référentielle.
    
    Returns:
        Response: Redirection avec message de confirmation ou d'erreur
    """
    if 'user_id' not in session or session['role'] != 'admin':
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
    """
    Traite l'ajout d'un nouveau type d'article.
    Accessible uniquement aux administrateurs via méthode POST.
    
    Le type est associé à une catégorie existante et son nom
    doit être unique au sein de cette catégorie.
    
    Returns:
        Response: Redirection avec message de confirmation ou d'erreur
    """
    if 'user_id' not in session or session['role'] != 'admin':
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
    """
    Met à jour un type existant identifié par son ID.
    Accessible uniquement aux administrateurs via méthode POST.
    
    Args:
        id (int): Identifiant du type à modifier
    
    Permet la modification du nom et/ou de la catégorie associée
    avec vérification des contraintes d'unicité.
    
    Returns:
        Response: Redirection avec message de confirmation ou d'erreur
    """
    if 'user_id' not in session or session['role'] != 'admin':
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
        
        # Vérification de l'unicité (sauf pour l'élément en cours)
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
    """
    Supprime un type identifié par son ID.
    Accessible uniquement aux administrateurs via méthode POST.
    
    Args:
        id (int): Identifiant du type à supprimer
    
    Vérifie l'absence d'articles associés avant de procéder à la suppression
    pour maintenir l'intégrité référentielle.
    
    Returns:
        Response: Redirection avec message de confirmation ou d'erreur
    """
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('index'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Vérification des dépendances
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

    try:
        cur = mysql.connection.cursor()

        # Statistiques laboratoires
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
                COUNT(DISTINCT t.id_type) as types_count
            FROM laboratoire l
            LEFT JOIN stock_laboratoire sl ON l.id_laboratoire = sl.id_laboratoire
            LEFT JOIN stock_magasin sm ON sl.id_lot = sm.id_lot
            LEFT JOIN article a ON sm.id_article = a.id_article
            LEFT JOIN type t ON a.id_type = t.id_type
            GROUP BY l.id_laboratoire, t.nom_type
        """)
        lab_types_data = cur.fetchall()

       # Préparation données graphique
        types = sorted({lt['type_article'] for lt in lab_types_data if lt['type_article']}) 
        lab_types_dict = defaultdict(dict)
        
        for lt in lab_types_data:
            lab_id = lt['id_laboratoire']
            lab_types_dict[lab_id][lt['type_article']] = lt['types_count']

        # Création des paires catégorie/données
        type_data = []
        for type_name in types:
            counts = []
            for lab in labs_stats:
                counts.append(lab_types_dict[lab['id_laboratoire']].get(type_name, 0))
            type_data.append(counts)

        paired_data = list(zip(types, type_data))

        return render_template('statistiques.html',
        lab_names=[lab['nom_laboratoire'] for lab in labs_stats],
        tp_counts=[lab['nb_tp'] for lab in labs_stats],
        types=types,
        type_data=type_data)

    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close()


# === Routes pour la gestion des reçus ===
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
    if 'user_id' not in session or session.get('role') != 'admin':
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

        

if __name__ == '__main__':
    # Création des utilisateurs dans un contexte d'application
    with app.app_context():
        create_default_users()
    
    # Lancer le serveur en mode debug accessible sur le réseau
    app.run(host='0.0.0.0', port=5000, debug=True)
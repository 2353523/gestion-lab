import os
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from flask_session import Session 
from flask_wtf.csrf import CSRFProtect
import mysql.connector




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

@app.route('/stocks')
def stocks_overview():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Récupération données magasin
        cur.execute("""
                SELECT COUNT(a.id_article) as nb_articles, 
                    SUM(sm.quantite) as total_quantite
                FROM stock_magasin sm
                JOIN article a ON sm.id_article = a.id_article  # ✅ Correction ici
            """)
        magasin = cur.fetchone()
        
        # Récupération données labos
        cur.execute("""
                SELECT l.id_laboratoire, l.nom_laboratoire, 
                    COUNT(sl.id_article) as nb_articles,
                    SUM(sl.quantite) as total_quantite
                FROM laboratoire l
                LEFT JOIN stock_laboratoire sl ON l.id_laboratoire = sl.id_laboratoire
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
    
    cur = mysql.connection.cursor()
    try:
        # Modifier la requête SQL pour inclure les IDs
        cur.execute("""
            SELECT a.id_article, a.nom_article, a.unite_mesure, 
                sm.quantite AS quantite_magasin,
                t.id_type, t.nom_type,
                c.id_categorie, c.nom_categorie
            FROM article a
            JOIN stock_magasin sm ON a.id_article = sm.id_article  
            JOIN type t ON a.id_type = t.id_type
            JOIN categorie c ON t.id_categorie = c.id_categorie
        """)
        stock = cur.fetchall()

        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()

    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
    finally:
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
        # Récupération des catégories/types
        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()

        if request.method == 'POST':
            nom = request.form['nom']
            unite = request.form['unite']
            quantite = int(request.form['quantite'])
            id_type = int(request.form['type'])

            # Transaction atomique
            with mysql.connection.cursor() as trans_cur:
                # 1. Insertion article
                # Insert article
                trans_cur.execute("""
                    INSERT INTO article (nom_article, unite_mesure, id_type)
                    VALUES (%s, %s, %s)
                """, (nom, unite, id_type))
                id_article = trans_cur.lastrowid

                # Insert stock
                trans_cur.execute("""
                    INSERT INTO stock_magasin (id_article, quantite)
                    VALUES (%s, %s)
                """, (id_article, quantite))

                mysql.connection.commit()
                flash("Article créé avec stock initial", "success")
                return redirect(url_for('stock_magasin'))

        return render_template('stock/ajouter_article.html',
                             categories=categories,
                             types=types)

    except Exception as e:
        mysql.connection.rollback()
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

            with mysql.connection.cursor() as trans_cur:
                # Mise à jour article
                trans_cur.execute("""
                    UPDATE article SET
                        nom_article = %s,
                        unite_mesure = %s,
                        id_type = %s
                    WHERE id_article = %s
                """, (nom, unite, id_type, id))

                # Mise à jour stock magasin
                trans_cur.execute("""
                    UPDATE stock_magasin SET
                        quantite = %s
                    WHERE id_article = %s
                """, (quantite, id))

                mysql.connection.commit()
                flash("Modifications enregistrées", "success")
                return redirect(url_for('stock_magasin'))

        # Récupération données existantes
        cur.execute("""
            SELECT a.*, sm.quantite, t.id_categorie 
            FROM article a
            JOIN stock_magasin sm ON a.id_article = sm.id_article
            JOIN type t ON a.id_type = t.id_type
            WHERE a.id_article = %s
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
            # La suppression en cascade s'occupe du stock_magasin
            trans_cur.execute("DELETE FROM article WHERE id_article = %s", (id,))
            mysql.connection.commit()
            flash("Article et stock associé supprimés", "success")

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

        if request.method == 'POST':
            article_id = request.form['article_id']
            quantite = int(request.form['quantite'])
            action = request.form['action']
            
            try:
                with mysql.connection.cursor() as trans_cur:
                    if action == 'ajouter':
                        # Vérification stock magasin avec verrou
                        trans_cur.execute("""
                            SELECT quantite FROM stock_magasin 
                            WHERE id_article = %s FOR UPDATE
                        """, (article_id,))
                        stock = trans_cur.fetchone()
                        
                        if not stock or stock['quantite'] < quantite:
                            raise Exception("Stock magasin insuffisant")

                        # Mise à jour transactionnelle
                        trans_cur.execute("""
                            UPDATE stock_magasin
                            SET quantite = quantite - %s
                            WHERE id_article = %s
                        """, (quantite, article_id))
                        
                        trans_cur.execute("""
                            INSERT INTO stock_laboratoire (id_article, id_laboratoire, quantite)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE quantite = quantite + VALUES(quantite)
                        """, (article_id, id_lab, quantite))

                    elif action == 'retirer':
                        # Vérification stock labo
                        trans_cur.execute("""
                            SELECT quantite FROM stock_laboratoire 
                            WHERE id_article = %s AND id_laboratoire = %s FOR UPDATE
                        """, (article_id, id_lab))
                        stock = trans_cur.fetchone()
                        
                        if not stock or stock['quantite'] < quantite:
                            raise Exception("Stock laboratoire insuffisant")

                        # Mise à jour transactionnelle
                        trans_cur.execute("""
                            UPDATE stock_laboratoire
                            SET quantite = quantite - %s
                            WHERE id_article = %s AND id_laboratoire = %s
                        """, (quantite, article_id, id_lab))
                        
                        trans_cur.execute("""
                            UPDATE stock_magasin
                            SET quantite = quantite + %s
                            WHERE id_article = %s
                        """, (quantite, article_id))

                    mysql.connection.commit()
                    flash("Opération réussie", "success")

            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur : {str(e)}", "danger")

        # Récupération des données
        cur.execute("""
            SELECT a.id_article, a.nom_article, a.unite_mesure,
                   sl.quantite, t.id_categorie, t.id_type
            FROM stock_laboratoire sl
            JOIN article a ON sl.id_article = a.id_article
            JOIN type t ON a.id_type = t.id_type
            WHERE sl.id_laboratoire = %s
        """, (id_lab,))
        stock = cur.fetchall()

        cur.execute("""
            SELECT a.*, sm.quantite AS stock_disponible 
            FROM article a
            JOIN stock_magasin sm ON a.id_article = sm.id_article
        """)
        articles = cur.fetchall()

        cur.execute("SELECT * FROM categorie")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()

        type_categories = {t['id_type']: t['id_categorie'] for t in types}
        categories_dict = {c['id_categorie']: c['nom_categorie'] for c in categories}
        types_dict = {t['id_type']: t['nom_type'] for t in types}

    except Exception as e:
        flash(f"Erreur base de données : {str(e)}", "danger")
    finally:
        cur.close()

    return render_template('stock/stock_lab.html',
                         labo=labo,
                         stock=stock,
                         articles=articles,
                         categories=categories,
                         types=types,
                         type_categories=type_categories,
                         categories_dict=categories_dict,
                         types_dict=types_dict)


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

if __name__ == '__main__':
    # Création des utilisateurs dans un contexte d'application
    with app.app_context():
        create_default_users()
    
    # Lancer le serveur en mode debug accessible sur le réseau
    app.run(host='0.0.0.0', port=5000, debug=True)
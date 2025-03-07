import os
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.secret_key = 'clé_secrète_pour_production'  

# Configuration MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gestion_lab'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.context_processor
def inject_datetime():
    return dict(datetime=datetime, timedelta=timedelta)


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


@app.route('/creer_tp', methods=['GET', 'POST'])
def creer_tp():
    CRENEAUX = {
        'P1': ('08:00', '09:30'),
        'P2': ('09:45', '11:15'),
        'P3': ('11:30', '13:00'),
        'P4': ('15:10', '16:40'),
        'P5': ('17:00', '18:30')
    }

    # Récupération des paramètres initiaux
    default_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    default_periode = request.args.get('periode', None)

    # Récupération des données pour les listes déroulantes
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

            # Validation
            if not all([data['nom_tp'], data['id_prof'], data['id_matiere'], data['date_tp']]):
                flash("Tous les champs obligatoires (*) doivent être remplis", "danger")
                return render_template('creer_tp.html',
                                    professeurs=professeurs,
                                    matieres=matieres,
                                    CRENEAUX=CRENEAUX,
                                    laboratoires=laboratoires)

            if not data['periodes']:
                flash("Veuillez sélectionner au moins un créneau horaire", "danger")
                return render_template('creer_tp.html',
                                    professeurs=professeurs,
                                    matieres=matieres,
                                    CRENEAUX=CRENEAUX,
                                    laboratoires=laboratoires)

            # Calcul des horaires combinés
            heures = [CRENEAUX[p] for p in data['periodes'] if p in CRENEAUX]
            if not heures:
                flash("Créneau(x) horaire(s) invalide(s)", "danger")
                return render_template('creer_tp.html',
                                    professeurs=professeurs,
                                    matieres=matieres,
                                    CRENEAUX=CRENEAUX,
                                    laboratoires=laboratoires)

            # Tri des créneaux par ordre chronologique
            heures.sort(key=lambda x: x[0])
            
            # Début = première période, Fin = dernière période
            debut = heures[0][0]
            fin = heures[-1][1]

            # Conversion en datetime
            heure_debut = datetime.strptime(f"{data['date_tp']} {debut}", "%Y-%m-%d %H:%M")
            heure_fin = datetime.strptime(f"{data['date_tp']} {fin}", "%Y-%m-%d %H:%M")

            # Vérification de la cohérence
            if heure_debut >= heure_fin:
                flash("Combinaison de créneaux invalide", "danger")
                return render_template('creer_tp.html',
                                    professeurs=professeurs,
                                    matieres=matieres,
                                    CRENEAUX=CRENEAUX,
                                    laboratoires=laboratoires)

            # Insertion en base
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO tp (
                    nom_tp, heure_debut, heure_fin, annee_scolaire,
                    id_laboratoire, id_matiere, id_prof
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                data['nom_tp'], heure_debut, heure_fin, data['annee_scolaire'],
                data['id_laboratoire'], data['id_matiere'], data['id_prof']
            ))
            mysql.connection.commit()
            flash("TP créé avec succès!", "success")
            return redirect(url_for('index'))

        except ValueError as e:
            flash(f"Format de date invalide : {str(e)}", "danger")
            return render_template('creer_tp.html',
                                professeurs=professeurs,
                                matieres=matieres,
                                CRENEAUX=CRENEAUX,
                                laboratoires=laboratoires)
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erreur MySQL: {str(e)}", "danger")
            return render_template('creer_tp.html',
                                professeurs=professeurs,
                                matieres=matieres,
                                CRENEAUX=CRENEAUX,
                                laboratoires=laboratoires)

    return render_template('creer_tp.html',
                         professeurs=professeurs,
                         matieres=matieres,
                         laboratoires=laboratoires,
                         CRENEAUX=CRENEAUX,
                         default_date=default_date,
                         default_periodes=[default_periode] if default_periode else [])

@app.route('/editer_tp/<int:id>', methods=['GET', 'POST'])
def editer_tp(id):
    CRENEAUX = {
        'P1': ('08:00', '09:30'),
        'P2': ('09:45', '11:15'),
        'P3': ('11:30', '13:00'),
        'P4': ('15:10', '16:40'),
        'P5': ('17:00', '18:30')
    }

    cur = mysql.connection.cursor()
    try:
        # Récupérer le TP existant
        cur.execute("SELECT * FROM tp WHERE id_tp = %s", (id,))
        tp = cur.fetchone()

        if not tp:
            flash("TP introuvable", "danger")
            return redirect(url_for('index'))

        # Déterminer les créneaux existants
        periodes_selectionnes = []
        debut_existant = tp['heure_debut'].strftime("%H:%M")
        fin_existante = tp['heure_fin'].strftime("%H:%M")
        
        for periode, (debut, fin) in CRENEAUX.items():
            if (datetime.strptime(debut, "%H:%M") >= datetime.strptime(debut_existant, "%H:%M") and
                datetime.strptime(fin, "%H:%M") <= datetime.strptime(fin_existante, "%H:%M")):
                periodes_selectionnes.append(periode)

        if request.method == 'POST':
            data = {
                'nom_tp': request.form['nom_tp'].strip(),
                'id_prof': request.form.get('id_prof', '').strip(),
                'id_matiere': request.form.get('id_matiere', '').strip(),
                'id_laboratoire': request.form.get('id_laboratoire', '').strip() or None,
                'date_tp': request.form['date_tp'].strip(),
                'periodes': request.form.getlist('periodes'),
                'annee_scolaire': request.form['annee_scolaire'].strip()
            }

            # Validation
            if not all([data['nom_tp'], data['id_prof'], data['id_matiere'], data['date_tp']]):
                flash("Tous les champs obligatoires (*) doivent être remplis", "danger")
                return redirect(url_for('editer_tp', id=id))

            if not data['periodes']:
                flash("Veuillez sélectionner au moins un créneau horaire", "danger")
                return redirect(url_for('editer_tp', id=id))

            # Calcul des horaires combinés
            heures = [CRENEAUX[p] for p in data['periodes'] if p in CRENEAUX]
            if not heures:
                flash("Créneau(x) horaire(s) invalide(s)", "danger")
                return redirect(url_for('editer_tp', id=id))

            # Tri des créneaux
            heures.sort(key=lambda x: x[0])
            debut = heures[0][0]
            fin = heures[-1][1]

            try:
                heure_debut = datetime.strptime(f"{data['date_tp']} {debut}", "%Y-%m-%d %H:%M")
                heure_fin = datetime.strptime(f"{data['date_tp']} {fin}", "%Y-%m-%d %H:%M")
                
                if heure_debut >= heure_fin:
                    flash("Combinaison de créneaux invalide", "danger")
                    return redirect(url_for('editer_tp', id=id))

                # Mise à jour
                cur.execute("""
                    UPDATE tp SET
                        nom_tp = %s,
                        heure_debut = %s,
                        heure_fin = %s,
                        annee_scolaire = %s,
                        id_laboratoire = %s,
                        id_matiere = %s,
                        id_prof = %s
                    WHERE id_tp = %s
                """, (
                    data['nom_tp'], 
                    heure_debut, 
                    heure_fin, 
                    data['annee_scolaire'],
                    data['id_laboratoire'], 
                    data['id_matiere'], 
                    data['id_prof'], 
                    id
                ))
                mysql.connection.commit()
                flash("TP modifié avec succès!", "success")
                return redirect(url_for('index'))

            except ValueError as e:
                flash(f"Format de date invalide : {str(e)}", "danger")
                return redirect(url_for('editer_tp', id=id))
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur MySQL: {str(e)}", "danger")
                return redirect(url_for('editer_tp', id=id))

        # Récupération des données pour le template
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
                            laboratoires=laboratoires)

    except Exception as e:
        flash(f"Erreur système: {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        cur.close()

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

@app.route('/emploi')
def emploi():
    CRENEAUX = {
        'P1': ('08:00', '09:30'),
        'P2': ('09:45', '11:15'),
        'P3': ('11:30', '13:00'),
        'P4': ('15:10', '16:40'),
        'P5': ('17:00', '18:30')
    }

    try:
        week_offset = int(request.args.get('week_offset', 0))
        today = datetime.now().date()
        start_of_week = today + timedelta(weeks=week_offset) - timedelta(days=today.weekday())
        days_of_week = [start_of_week + timedelta(days=i) for i in range(7)]
        
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT 
                tp.id_tp,
                tp.nom_tp,
                tp.heure_debut,
                tp.heure_fin,
                l.nom_laboratoire,
                p.prenom,
                p.nom,
                m.nom_matiere
            FROM tp
            JOIN professeur p ON tp.id_prof = p.id_prof
            LEFT JOIN laboratoire l ON tp.id_laboratoire = l.id_laboratoire
            JOIN matiere m ON tp.id_matiere = m.id_matiere
            WHERE YEARWEEK(tp.heure_debut) = YEARWEEK(%s)
            ORDER BY tp.heure_debut
        """, (start_of_week,))
        
        tps = {}
        for tp in cur.fetchall():
            day = tp['heure_debut'].date()
            period = get_period(tp['heure_debut'].time())
            key = f"{day}-{period}"
            tps[key] = tp

        return render_template('emplois/emploi.html',
                            days=days_of_week,
                            tps=tps,
                            week_offset=week_offset,
                            CRENEAUX=CRENEAUX)

    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for('index'))
    finally:
        if 'cur' in locals():
            cur.close()

def get_period(time):
    periods = {
        'P1': ('08:00', '09:30'),
        'P2': ('09:45', '11:15'),
        'P3': ('11:30', '13:00'),
        'P4': ('15:10', '16:40'),
        'P5': ('17:00', '18:30')
    }
    time_str = time.strftime('%H:%M')
    for period, (start, end) in periods.items():
        if start <= time_str <= end:
            return period
    return None

if __name__ == '__main__':
    app.run(debug=True)
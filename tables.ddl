-- ==============================================================================
-- PARTIE 1 : NETTOYAGE COMPLET (On repart à zéro pour éviter les conflits)
-- ==============================================================================
DROP TABLE IF EXISTS VALEURS_C CASCADE;
DROP TABLE IF EXISTS MODALITE CASCADE;
DROP TABLE IF EXISTS PLAGE CASCADE;
DROP TABLE IF EXISTS VARIABLE CASCADE;
DROP TABLE IF EXISTS RUBRIQUE CASCADE;
DROP TABLE IF EXISTS SOLUTION CASCADE;
DROP TABLE IF EXISTS DEMANDE CASCADE;
DROP TABLE IF EXISTS ENTRETIEN CASCADE;

-- ==============================================================================
-- PARTIE 2 : CRÉATION DES TABLES DE DONNÉES (Source de vérité)
-- ==============================================================================
CREATE TABLE ENTRETIEN(
   NUM SERIAL,
   DATE_ENT DATE,
   MODE SMALLINT,
   DUREE SMALLINT,
   SEXE SMALLINT,
   AGE SMALLINT,
   VIENT_PR SMALLINT,
   SIT_FAM VARCHAR(2),
   ENFANT SMALLINT,
   MODELE_FAM SMALLINT,
   PROFESSION SMALLINT,
   RESS SMALLINT,
   ORIGINE VARCHAR(2),
   COMMUNE VARCHAR(50),
   PARTENAIRE VARCHAR(50),
   PRIMARY KEY(NUM)
);

-- Commentaires essentiels pour l'extraction automatique
COMMENT ON TABLE ENTRETIEN IS 'La table entretien est l''une des tables de stockage des données';
COMMENT ON COLUMN ENTRETIEN.NUM IS 'Identifiant de l''entretien, Rubrique Entretien';
COMMENT ON COLUMN ENTRETIEN.DATE_ENT IS 'Date de l''entretien Valeur par défaut : jour courant, Rubrique Entretien';
COMMENT ON COLUMN ENTRETIEN.MODE IS 'Mode de l''entretien (1 : RDV; 2 : Sans RDV;3 : Téléphonique;4 : Courrier;5 : Mail), Rubrique Entretien';
COMMENT ON COLUMN ENTRETIEN.DUREE IS 'Durée de l''entretien (1 : - de 15 min;2 : 15 à 30 min;3 : 30 à 45 min;4 : 45 à 60 min;5 : + de 60 min), Rubrique Entretien';
COMMENT ON COLUMN ENTRETIEN.SEXE IS 'Sexe si une personne, couple ou professionnel (1 : Homme;2 : Femme;3 : Couple;4 : Professionnel), Rubrique Usager';
COMMENT ON COLUMN ENTRETIEN.AGE IS 'Age de la personne (1 : -18 ans;2 : 18-25 ans;3 : 26-40 ans;4 : 41-60 ans;5 : + 60 ans), Rubrique Usager';
COMMENT ON COLUMN ENTRETIEN.VIENT_PR IS 'Vient pour (1 : Soi;2 : Conjoint;3 : Parent;4 : Enfant;5 : Personne morale;6 : Autre), Rubrique Usager';
COMMENT ON COLUMN ENTRETIEN.SIT_FAM IS 'Situation familiale (1 : Célibataire;2 : Concubin;3 : Pacsé;4 : Marié;5 : Séparé/divorcé;5a : Séparé/divorcé Sans enf. à charge;5b : Séparé/divorcé Avec enf. en garde alternée;5c : Séparé/divorcé Avec enf. en garde principale;5d : Séparé/divorcé Avec enf. en droit de visite/hbgt;5e : Séparé/divorcé Parent isolé; 5f : Séparé/divorcé Séparés sous le même toit;6 : Veuf/ve;6a : Veuf/ve Sans enf. à charge;6b : Veuf/ve Avec enf. à charge;7 : Non renseigné), Rubrique Usager';
COMMENT ON COLUMN ENTRETIEN.ENFANT IS 'Enfant(s) à charge (1;2;3;4;5;6;7;8;9;10;11;12;13), Rubrique Usager';
COMMENT ON COLUMN ENTRETIEN.MODELE_FAM IS 'Si famille avec enfant, il s''agit du modèle familial (1 : Famille traditionnelle;2 : Famille monoparentale;3 : Famille recomposée), Rubrique Usager';
COMMENT ON COLUMN ENTRETIEN.PROFESSION IS 'Profession (1 : Scolaire/étudiant/formation;2 : Pêcheur/agriculteur;3 : Chef d''entreprise;4 : Libéral;5 : Militaire;6 : Employé;7 : Ouvrier;8 : Cadre;9 : Retraité;10 : En recherche d''emploi;11 : Sans profession;12 : Non renseigné) , Rubrique Usager';
COMMENT ON COLUMN ENTRETIEN.RESS IS 'Revenus, ressource principale (1 : Salaire;2 : Revenus pro.;3 : Retraite/réversion;4 : Allocations chômage;5 : RSA;6 : AAH/invalidité;7 : IJSS;8 : Bourse d''études;9 : Sans revenu;10 : Autre;11 : Non renseigné) , Rubrique Usager';
COMMENT ON COLUMN ENTRETIEN.ORIGINE IS 'Origine de la demande (1a : Com Bouche à oreille;1b : Com Internet;1c : Com Presse;2a : Déjà venu Suite;2b : Déjà venu Autre;3a : Pro droit Tribunaux;3b : Pro droit Police;3c : Pro droit;4a : Admin CAF;4b : Admin DIRECCTE;4c : Admin MFS;4d : Admin Mairie;4e : Admin Autre;5a : Santé AS;5b : Santé Educ;5c : Santé Pro;5d : Santé Jeunesse;5e : Santé RIPAM;6a : Asso France Victimes;6b : Asso Conso;6c : Asso ADIL;6d : Asso UDAF;6e : Asso accès droit;6f : Asso Autre;7a : Privé PJ;7b : Privé Autre;8 : Action coll;9 : 3949 NUAD) , Rubrique Repérage du dispositif';
COMMENT ON COLUMN ENTRETIEN.COMMUNE IS 'Commune de résidence (Vannes;Auray;Arradon;Séné;Theix-Noyalo;Plescop;Saint-Avé;Grand-Champ;Elven;Sarzeau;Muzillac;Questembert;Ploërmel;Locminé;Pontivy;Lorient;Hennebont;Lanester;Plouay;Quiberon;Autre), Rubrique Résidence';
COMMENT ON COLUMN ENTRETIEN.PARTENAIRE IS 'Partenaire lors de l''entretien (Permanence juridique Vannes;Permanence juridique Auray;Permanence juridique Questembert;Permanence avocat généraliste;Permanence avocat mineurs;Permanence notaire;Permanence conciliateur de justice;Permanence délégué du défenseur des droits), Rubrique Partenaire';

CREATE TABLE DEMANDE(
   NUM INTEGER,
   POS SMALLINT,
   NATURE VARCHAR(50) NOT NULL,
   PRIMARY KEY(NUM, POS),
   FOREIGN KEY(NUM) REFERENCES ENTRETIEN(NUM)
);
COMMENT ON TABLE DEMANDE IS 'La table demande est l''une des tables de stockage des données';
COMMENT ON COLUMN DEMANDE.NATURE IS 'Nature de la demande (1a : Famille Union;1b : Famille Séparation;4a : Civil Responsabilité;7a : Pénal Auteur;7b : Pénal Victime), Rubrique Demande';

CREATE TABLE SOLUTION(
   NUM INTEGER,
   POS SMALLINT,
   NATURE VARCHAR(50) NOT NULL,
   PRIMARY KEY(NUM, POS),
   FOREIGN KEY(NUM) REFERENCES ENTRETIEN(NUM)
);
COMMENT ON TABLE SOLUTION IS 'La table solution est l''une des tables de stockage des données';
COMMENT ON COLUMN SOLUTION.NATURE IS 'Nature de la solution (1 : Info;2a : Aide démarches;3a : Rédaction;4a : Orientation Avocat), Rubrique Solution';

-- ==============================================================================
-- PARTIE 3 : CRÉATION DES TABLES DE MÉTADONNÉES (Structure)
-- ==============================================================================
CREATE TABLE RUBRIQUE(
   POS SERIAL,
   LIB VARCHAR(50) NOT NULL,
   PRIMARY KEY(POS)
);

CREATE TABLE VARIABLE(
   TAB VARCHAR(30),
   POS SMALLINT,
   LIB VARCHAR(50) NOT NULL,
   COMMENTAIRE VARCHAR(4000),
   MOIS_DEBUT_VALIDITE SMALLINT NOT NULL DEFAULT 1,
   MOIS_FIN_VALIDITE SMALLINT NOT NULL DEFAULT 12,
   TYPE_V VARCHAR(8) NOT NULL,
   DEFVAL SMALLINT,
   EST_CONTRAINTE BOOLEAN NOT NULL DEFAULT FALSE,
   POS_R INTEGER,
   RUBRIQUE INTEGER,
   PRIMARY KEY(TAB, POS),
   UNIQUE(TAB, LIB),
   FOREIGN KEY(RUBRIQUE) REFERENCES RUBRIQUE(POS)
);

CREATE TABLE PLAGE(
   TAB VARCHAR(30),
   POS SMALLINT,
   VAL_MIN SMALLINT,
   VAL_MAX SMALLINT,
   PRIMARY KEY(TAB, POS),
   FOREIGN KEY(TAB, POS) REFERENCES VARIABLE(TAB, POS)
);

CREATE TABLE MODALITE(
   TAB VARCHAR(30),
   POS SMALLINT,
   CODE VARCHAR(10),
   POS_M SMALLINT NOT NULL,
   LIB_M VARCHAR(100) NOT NULL,
   PRIMARY KEY(TAB, POS, CODE),
   FOREIGN KEY(TAB, POS) REFERENCES VARIABLE(TAB, POS)
);

CREATE TABLE VALEURS_C(
   TAB VARCHAR(30),
   POS SMALLINT,
   POS_C SMALLINT,
   LIB VARCHAR(100) NOT NULL,
   PRIMARY KEY(TAB, POS, POS_C),
   FOREIGN KEY(TAB, POS) REFERENCES VARIABLE(TAB, POS)
);

-- ==============================================================================
-- PARTIE 4 : PEUPLEMENT AUTOMATIQUE (Le moteur d'extraction)
-- ==============================================================================

-- 4.1. Créer les rubriques
INSERT INTO RUBRIQUE (LIB) VALUES
('Entretien'), ('Usager'), ('Demande'), ('Solution'), 
('Repérage du dispositif'), ('Résidence'), ('Partenaire');

-- 4.2. Remplir VARIABLE (C'est ici que l'erreur se produisait avant)
INSERT INTO VARIABLE (TAB, POS, LIB, COMMENTAIRE, TYPE_V, POS_R, RUBRIQUE)
SELECT 
    UPPER(TABLE_NAME),
    ordinal_position,
    UPPER(COLUMN_NAME),
    TRIM(SPLIT_PART(pg_catalog.col_description(format('%s.%s',isc.table_schema,isc.table_name)::regclass::oid,isc.ordinal_position), ', Rubrique', 1)),
    'MOD', 
    1,
    NULL 
FROM information_schema.columns isc
WHERE UPPER(TABLE_NAME) IN ('ENTRETIEN','DEMANDE','SOLUTION')
AND table_schema = 'public'; 

-- 4.3. Lier les Variables aux Rubriques
UPDATE VARIABLE V 
SET RUBRIQUE = (
    SELECT R.POS 
    FROM RUBRIQUE R
    WHERE R.LIB = TRIM(
        SUBSTRING(
            pg_catalog.col_description(format('public.%s', V.TAB)::regclass::oid, V.POS) 
            FROM 'Rubrique (.*)'
        )
    )
);

-- 4.4. Corriger les types (Numérique et Chaine)
UPDATE VARIABLE SET TYPE_V='NUM' WHERE TAB='ENTRETIEN' AND POS=9; -- Enfant
UPDATE VARIABLE SET TYPE_V='CHAINE' WHERE TAB='ENTRETIEN' AND POS IN (14, 15); -- Commune, Partenaire

-- 4.5. Insérer la PLAGE (Maintenant ça va marcher car VARIABLE(ENTRETIEN, 9) existe)
INSERT INTO PLAGE (TAB,POS,VAL_MIN,VAL_MAX) 
VALUES ('ENTRETIEN', 9, 0, 13);

-- 4.6. Extraire les MODALITÉS (Format "1 : Libellé")
INSERT INTO MODALITE (TAB, POS, CODE, POS_M, LIB_M)
SELECT 
    UPPER(isc.table_name),
    isc.ordinal_position,
    TRIM(split_part(elem, ' : ', 1)),
    nr,
    TRIM(split_part(elem, ' : ', 2))
FROM 
    information_schema.columns isc,
    LATERAL unnest(string_to_array(
        substring(
            pg_catalog.col_description(format('%s.%s',isc.table_schema,isc.table_name)::regclass::oid,isc.ordinal_position) 
            FROM '\((.*)\),'
        ), 
        ';'
    )) WITH ORDINALITY AS a(elem, nr)
WHERE 
    UPPER(TABLE_NAME) IN ('ENTRETIEN', 'DEMANDE', 'SOLUTION')
    AND table_schema = 'public'
    AND isc.ordinal_position NOT IN (14, 15) 
    AND position(' : ' in elem) > 0;

-- 4.7. Extraire les LISTES SIMPLES (Format "A;B;C")
INSERT INTO VALEURS_C (TAB, POS, LIB, POS_C)
SELECT 
    UPPER(isc.table_name),
    isc.ordinal_position,
    TRIM(a.elem_text),
    a.nr
FROM 
    information_schema.columns isc,
    LATERAL unnest(string_to_array(
        substring(
            pg_catalog.col_description(format('%s.%s',isc.table_schema,isc.table_name)::regclass::oid,isc.ordinal_position) 
            FROM '\((.*)\)'
        ), 
        ';'
    )) WITH ORDINALITY AS a(elem_text, nr)
WHERE 
    UPPER(TABLE_NAME) = 'ENTRETIEN' 
    AND table_schema = 'public'
    AND isc.ordinal_position IN (14, 15);

-- Vérification finale
SELECT COUNT(*) as nb_variables FROM VARIABLE;
-- Doit retourner environ 18






-- 1. Création de la table AGGLO (Communautés de communes)
CREATE TABLE AGGLO(
   CODE_A SERIAL,
   NOM_A VARCHAR(50) NOT NULL,
   ACRONYME VARCHAR(20) NOT NULL,
   URL VARCHAR(100), -- Agrandissement par sécurité
   PRIMARY KEY(CODE_A)
);

-- 2. Création de la table COMMUNE (Liée à Agglo)
CREATE TABLE COMMUNE(
   CODE_C SERIAL,
   NOM_C VARCHAR(50) NOT NULL,
   INSEE VARCHAR(5),
   URL VARCHAR(100),
   CODE_A INTEGER NULL,
   PRIMARY KEY(CODE_C),
   FOREIGN KEY(CODE_A) REFERENCES AGGLO(CODE_A)
);

-- 3. Création de la table QUARTIER (Liée à Commune)
CREATE TABLE QUARTIER(
   CODE_Q SERIAL,
   NOM_Q VARCHAR(50) NOT NULL,
   INSEE_IRIS VARCHAR(10),
   CODE_C INTEGER NOT NULL,
   PRIMARY KEY(CODE_Q),
   FOREIGN KEY(CODE_C) REFERENCES COMMUNE(CODE_C)
);

-- 4. Insertion des AGGLOS
INSERT INTO AGGLO (NOM_A,ACRONYME) VALUES 
('Auray Quiberon Terre Atlantique', 'AQTA'),
('Golfe du Morbihan - Vannes agglomération','Vannes Agglo'),
('Questembert Communauté','Questembert CO'),
('Oust à Brocéliande Communauté','Oust à Broceliande'),
('Arc Sud Bretagne','ASB'),
('Ploërmel Communauté','Ploërmel Co');	

-- 5. Insertion des COMMUNES (Récupérées depuis vos métadonnées existantes)
-- On prend les libellés stockés dans VALEURS_C pour la colonne Commune (POS=14)
INSERT INTO COMMUNE (NOM_C) 
SELECT LIB 
FROM VALEURS_C 
WHERE TAB='ENTRETIEN' AND POS=14 AND LIB NOT LIKE 'HORS%';

-- 6. Mise à jour des liens AGGLO <-> COMMUNE
-- (Ceci associe les villes à leur agglo selon votre logique métier)
UPDATE COMMUNE SET CODE_A=1 WHERE NOM_C IN ('Auray','Belz','Brech','Camors','Carnac','Crac''h','Erdeven','Etel','Ile de Hoedic','Ile de Houat','Landaul','Landévant','La Trinité-sur-Mer','Locmariaquer','Locoal-Mendon','Ploemel','Plouharnel','Pluneret','Plumergat','Pluvigner','Quiberon','Ste-Anne-d''Auray','St-Philibert','St-Pierre-Quiberon');
UPDATE COMMUNE SET CODE_A=2 WHERE NOM_C IN ('Arradon','Arzon','Baden','Brandivy','Colpo','Elven','Grand-Champ','Ile d''Arz','Ile aux Moines','La Trinité-Surzur','Larmor-Baden','Le Bono','Le Hézo','Le Tour-du-Parc','Meucon','Monterblanc','Plaudren','Plescop','Ploeren','Plougoumelen','St-Armel','St-Avé','St-Gildas-de-Rhuys','St-Nolff','Sarzeau','Séné','Sulniac','Theix-Noyalo','Trédion','Treffléan','Vannes');
UPDATE COMMUNE SET CODE_A=3 WHERE NOM_C IN ('Questembert','Limerzel','Caden','Malensac','St-Gravé','Rochefort-en-Terre','Pluherlin','Molac','Le Cours','Larré','La Vraie-Croix','Berric','Lauzach');
-- ... (Vous pouvez ajouter les autres UPDATE ici si nécessaire)

-- 7. Insertion des QUARTIERS
-- Note: J'utilise une sous-requête pour trouver l'ID de Vannes ou Auray automatiquement
INSERT INTO QUARTIER(NOM_Q, CODE_C) VALUES 
('Auray Gumenen Goaner-Parco Pointer', (SELECT CODE_C FROM COMMUNE WHERE NOM_C='Auray')),
('Vannes Bourdonnaye', (SELECT CODE_C FROM COMMUNE WHERE NOM_C='Vannes')),
('Vannes Kercado', (SELECT CODE_C FROM COMMUNE WHERE NOM_C='Vannes')),
('Vannes Ménimur', (SELECT CODE_C FROM COMMUNE WHERE NOM_C='Vannes'));
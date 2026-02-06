---
title: "RDB, 1er Contrôle Continu, 2025"
course: "Bases de données relationnelles (RBD)"
ue: "201.3"
author: [Renaud Richardet]
date: "22.10.2025"
version: "1.0.14"

fontsize: 10pt
caption-justification: centering

header-includes: |
  \usepackage{xparse}
  \usepackage{pgffor}
  \NewDocumentCommand{\lignes}{m}{%
    \vspace{1cm}% espace avant la première ligne
    \foreach \i in {1,...,#1} {%
      \par\noindent\makebox[\linewidth]{\rule{\textwidth}{0.3pt}}
      \vspace{0.01cm}
    }
  }

  \newcommand{\nomprenom}{
    \vspace*{0cm}
    \noindent
    \textbf{Nom :} \underline{\hspace{5cm}}
    \hspace{1cm}
    \textbf{Prénom :} \underline{\hspace{5cm}}
    \vspace*{0.5cm}
  }

  \newif\ifsolution
  \solutionfalse  

  \usepackage{amssymb}
  \newcommand{\bigcheckbox}{\fbox{\rule{0pt}{1.7ex}\rule{1.6ex}{0pt}}}

---

\nomprenom


## Déroulement

- Ce contrôle continu se fait en 2 étapes : papier puis ordinateur
- 12h45 : distribution des instructions
- 12h50 à 13h10 : 1ère partie papier (20 minutes)
- 13h10 à 13h19 : pause (préparer ordinateur; rappel : pas d'écran externe)
- 13h20 à 14h00 : 2ème partie ordinateur (sur ISC Learn, 40 minutes)
- 14h00 rendu via ISC Learn. Pénalité de 1 point par minute de retard

En cas de problème technique hors de votre responsabilité, du temps supplémentaire vous sera accordé en conséquence.

## Matériel autorisé

- Pour la partie papier, vous avez uniquement droit à la donnée de ce test, du matériel pour écrire, des feuilles vierges et votre résumé A4 recto-verso.
- Idem pour la partie ordinateur, mais vous avez en plus droit à votre ordinateur et un clavier externe.
- Pendant la partie ordinateur, vous utiliserez uniquement un navigateur web et vous n'accéderez qu'à la page de l’examen. Aucun autre onglet, site ou logiciel ne doit être ouvert. Aucune extension, plugin, script, ou autre outil susceptible de vous fournir une aide n’est autorisé.

## Rendu

- Partie papier : questions
- Partie ordinateur : via ISC Learn

## Correction

- Seules les réponses lisibles seront corrigées
- Dans la partie ordinateur, ce n'est pas parce que votre requête SQL donne la bonne réponse qu'elle fait sens. Les requêtes qui fonctionnent mais ne font pas sens ne seront pas comptées comme justes.

\newpage
# Q1 Relations entre tables [3 pts + 0.5 pt bonus]

Soit les deux tables suivantes définies dans une RDB. On part du principe que cette RDB contient déjà des données dans ces tables.

```sql
CREATE TABLE Artist (
    ArtistId INTEGER PRIMARY KEY,
    Name NVARCHAR(120)
);

CREATE TABLE Album (
    AlbumId INTEGER PRIMARY KEY,
    Title NVARCHAR(160) NOT NULL,
    ArtistId INTEGER NOT NULL,
    FOREIGN KEY (ArtistId) REFERENCES Artist(ArtistId)
);
```

Parmi les affirmations suivantes, **indiquez “V” pour vrai et “F” pour faux dans chaque case** :

\bigcheckbox Il est possible d'insérer une artiste sans avoir créé d'album pour elle au préalable.  

\bigcheckbox Il est possible d'insérer un album pour une artiste qui elle-même n'existe pas dans la RDB.  

\bigcheckbox Il est possible d'insérer un album avec comme valeur pour ArtistId la valeur NULL.  
  
\bigcheckbox Il est possible d'insérer un album avec une valeur Title égale à la chaîne de caractères vide (`''`).  
  
\bigcheckbox Il est possible de modifier la valeur ArtistId d'un album vers une autre artiste, pour autant que cette autre artiste existe dans la RDB.  
  
\bigcheckbox Il est possible d'insérer plusieurs albums pour une même artiste.  
  
\bigcheckbox Un album peut être associé à plusieurs artistes différents.  
  
\bigcheckbox Il est possible de supprimer une artiste même si elle a des albums dans la RDB.  
  
\bigcheckbox Après avoir supprimé tous les albums et tous les artistes, il est possible d’insérer un nouvel album sans erreur.  
  
\bigcheckbox Il est possible d'executer le script `DELETE FROM Album; DELETE FROM Artist;` sans provoquer d'erreur.  
  
\bigcheckbox Il est possible d'executer le script `DROP TABLE Album; DROP TABLE Artist;` sans provoquer d'erreur.  
  
\bigcheckbox Une instruction `TRUNCATE` vide le contenu de la table mais conserve la structure de la table.  

Chaque bonne réponse rapporte 1/4 pt, chaque mauvaise réponse retire 1/10 pt.


\ifsolution

**Solution :**

1. vrai, la table Artist n'a aucune dépendance vers Album
2. faux car la FK ArtistId empêche cela
3. faux car la colonne ArtistId est defini comme NOT NULL dans Album
4. vrai, la chaîne de caractères vide n'est pas NULL
5. vrai, un UPDATE est autorisé si cette autre artiste existe dans la RDB
6. vrai, relation typique 1-n entre Artist et Album
7. faux, relation 1-n entre Artist et Album, pas n-m
8. faux, la FK bloque la suppression d'une artiste qui a des albums (sans ON DELETE CASCADE)
9. faux, après suppression de tous les albums et artistes, il n'existe plus d'ArtistId valide pour l'insertion d'un nouvel album
10. vrai, comme on DELETE d'abord Album puis Artist, pas d'erreur de violation de FK. L'inverse aurait provoqué une erreur.
11. vrai, comme on DROP d'abord Album puis Artist, pas de problème de violation de FK. L'inverse aurait provoqué une erreur.
12. vrai, c'est la définition de TRUNCATE TABLE.

\fi

**Question bonus [+ 0.5 pt]:** 

Que se passerait-il si la contrainte `FOREIGN KEY` comportait l'option `ON DELETE CASCADE` ? Quelles seraient les questions qui changeraient?

\ifsolution

**Solution :**

Seule la question 8 changerait: **vrai**, la suppression de l'artiste supprime automatiquement tous les albums associés.

\else

\lignes{3}


\fi



\vspace{1cm}
\newpage

\nomprenom

# Question 2 [6 pts]: Modélisation d'un système de gestion hospitalière

Vous êtes chargé.e de modéliser une RDB pour **gérer les rendez-vous** dans un hôpital. 

Tous les rendez-vous, quel que soit leur type, partagent ces caractéristiques :

- Un patient (1 seul)
- Une salle (1 seule) 
- Une date et heure du rendez-vous
- Un type parmi : 
    - consultation simple
    - examen radiologique
    - intervention chirurgicale
    - réanimation après contrôle-continu

Selon les besoins spécifiques de chaque rendez-vous (indépendamment de son type) :

- on peut avoir besoin d'équipement(s) ou pas
- on peut avoir besoin d'un.e membre du personnel médical ou pas


Par exemple :  
- Une consultation pourrait nécessiter 1 médecin  
- Un examen radiologique pourrait nécessiter 2 équipements  
- Une intervention chirurgicale pourrait nécessiter 2 chirurgiennes, 1 assistant et 4 équipements  
- Etc.  


Vous disposez de tables de base (voir schéma ci-dessous):  
- patients  
- personnel_medical  
- salles  
- equipements  


## Tâche 1 : Modélisation des différents types de rendez-vous  [4 pts]
Ajoutez une ou plusieurs tables à votre schéma afin de modéliser les rendez-vous.

Consignes :

- Ne rédigez pas de code SQL, mais ajoutez et dessinez une ou plusieurs tables dans votre schéma. Vous pouvez aussi modifier les tables existantes.
- Pour chaque clé primaire, indiquez "PK" à côté du nom de la colonne, et pour chaque clé étrangère, indiquez "FK"
- Reliez avec un trait les clés étrangères à leurs clés primaires correspondantes
- Prenez soin que toute la RDB soit en 3NF


## Tâche 2 : Requête SQL - Rendez-vous d'un patient  [2 pts]
Écrivez une requête SQL qui affiche tous les rendez-vous du patient avec l'id 5, en indiquant le type de rendez-vous, la date et heure du rendez-vous, les équipements s'il y en a, et les noms du personnel impliqués s'il y en a.

\newpage

\vspace{6cm}

![](tables_existantes.png){width=100%}

\ifsolution

Schéma des 4 tables existantes:

```sql
CREATE TABLE patients (
    id_patient INT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE
);

CREATE TABLE personnel_medical (
    id_personnel INT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    specialite VARCHAR(100)            -- év. normaliser
);

CREATE TABLE salles (
    id_salle INT PRIMARY KEY,
    nom_salle VARCHAR(100) NOT NULL,
    m2 DECIMAL(6,2)
);

CREATE TABLE equipements (
    id_equipement INT PRIMARY KEY,
    nom_equipement VARCHAR(100) NOT NULL,
    type_equipement VARCHAR(100)      -- év. normaliser
);

```

Les nouvelles tables à créer

```sql
-- pour rester en 3NF
CREATE TABLE type_rendez_vous (
    id_type_rendez_vous INT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL
);

CREATE TABLE rendez_vous (
    id_rendez_vous INT PRIMARY KEY,
    id_patient INT NOT NULL,
    id_salle INT NOT NULL,
    date_heure DATETIME NOT NULL,
    id_type_rendez_vous INT NOT NULL,
    FOREIGN KEY (id_patient) REFERENCES patients(id_patient),
    FOREIGN KEY (id_salle) REFERENCES salles(id_salle),
    FOREIGN KEY (id_type_rendez_vous) REFERENCES type_rendez_vous(id_type_rendez_vous)
);

-- table d'association
CREATE TABLE rdv_equipements (
    id_rendez_vous INT,
    id_equipement INT,
    PRIMARY KEY (id_rendez_vous, id_equipement),
    FOREIGN KEY (id_rendez_vous) REFERENCES rendez_vous(id_rendez_vous) 
        ON DELETE CASCADE,
    FOREIGN KEY (id_equipement) REFERENCES equipements(id_equipement)
);

-- table d'association
CREATE TABLE rdv_personnel (
    id_rendez_vous INT,
    id_personnel INT,
    role VARCHAR(100),
    PRIMARY KEY (id_rendez_vous, id_personnel),
    FOREIGN KEY (id_rendez_vous) REFERENCES rendez_vous(id_rendez_vous) 
        ON DELETE CASCADE,
    FOREIGN KEY (id_personnel) REFERENCES personnel_medical(id_personnel)
);

-- voici comment on pourrait insérer les données
INSERT INTO type_rendez_vous (id_type_rendez_vous, nom) VALUES
(1, 'consultation'),
(2, 'radiologie'),
(3, 'chirurgie'),
(4, 'réanimation après contrôle-continu'); 
```

![](rdv_solution.png){width=100%}


Solution tâche 2:

```sql
SELECT
    r.id_rendez_vous AS "id rdv",
    r.date_heure AS "date et heure",
    trv.nom AS "type de rdv",
    e.nom_equipement AS "équipement", -- peut être NULL
    pm.prenom || ' ' || pm.nom AS "nom du personnel", -- peut être NULL
FROM
    rendez_vous AS r
INNER JOIN
    type_rendez_vous AS trv 
    ON r.id_type_rendez_vous = trv.id_type_rendez_vous
LEFT JOIN
    rdv_equipements AS rde 
    ON r.id_rendez_vous = rde.id_rendez_vous
LEFT JOIN
    equipements AS e 
    ON rde.id_equipement = e.id_equipement
LEFT JOIN
    rdv_personnel AS rdp 
    ON r.id_rendez_vous = rdp.id_rendez_vous
LEFT JOIN
    personnel_medical AS pm 
    ON rdp.id_personnel = pm.id_personnel
WHERE
    r.id_patient = 5
ORDER BY
    r.date_heure, r.id_rendez_vous
```

\else

\newpage

\vspace{6cm}

\nomprenom

![](tables_existantes.png){width=100%}

\newpage

\vspace{6cm}

\nomprenom

![](tables_existantes.png){width=100%}

\fi

\ifsolution

\newpage

# Questions ordinateur

## Q1: Albums Pop

Affichez tous les albums de Pop (tous les albums qui contiennent au moins un morceau du genre "Pop")

Colonne de sortie: AlbumTitle

Ordonnez alphabétiquement par AlbumTitle


```sql
SELECT DISTINCT
    al.Title AS AlbumTitle
FROM Album al
JOIN Track t ON al.AlbumId = t.AlbumId
JOIN Genre g ON t.GenreId = g.GenreId
WHERE g.Name = 'Pop'
ORDER BY al.Title;
```

```
AlbumTitle
------------------------------------------------------------
Axé Bahia 2001
Frank
Instant Karma: The Amnesty International Campaign to Save Darfur
```

## Q2: Taille max

Vous savez qu’en SQL, on définit souvent une taille maximale pour une colonne de texte. Il est important que les données stockées dans une base relationnelle respectent cette limite, afin d’éviter des valeurs trop longues.

Par exemple, les titres d’albums (title) ne doivent pas dépasser la longueur maximale autorisée pour ce champ.



Ecrivez une requête qui affiche le pourcentage maximal de la longueur d’un titre d’album par rapport à la longueur maximale de la colonne.

- Arrondissez le pourcentage à l’entier le plus proche.
- Ajoutez le symbole % à la valeur.
- Nommez la colonne de sortie length_ratio_percent.


Solution:

```sql
SELECT
  CAST(ROUND(LENGTH(title) * 100.0 / 160, 0) AS INT) || '%' AS length_ratio_percent
FROM album
ORDER BY LENGTH(title) DESC
LIMIT 1;
```

Je vous invite a experimenter avec différentes possibilités:


```sql
SELECT 
  LENGTH(title) AS title_length,
  CAST(LENGTH(title) AS DOUBLE) / 160 AS length_ratio,
  CAST(LENGTH(title) / 160 AS DOUBLE) AS length_ratio2,
  CAST((LENGTH(title) * 100 / 160) AS DOUBLE) AS length_ratio3,
  ROUND(CAST((LENGTH(title) * 100 / 160) AS DOUBLE), 0 ) AS length_ratio4,
  ROUND(CAST((LENGTH(title) * 100 / 160) AS INT), 0 ) AS length_ratio5,
  CAST(ROUND(LENGTH(title) * 100.0 / 160, 0) AS INT) || '%' AS length_ratio_percent

FROM album
ORDER BY LENGTH(title) DESC
LIMIT 10;

```


## Q3: Dénormaliser


Dénormalisez les tables Artist, Album et Track en une seule requête SQL.

Choisissez des noms de colonnes adéquats.

Limitez votre output à 10 lignes, pour ne pas surcharger la RDB.

La solution de cette question est cachée. Rappel: même quand votre réponse est juste, l'interface reste rouge et affiche un message d'erreur.

```sql
SELECT
    ar.ArtistId,
    ar.Name AS ArtistName,
    al.AlbumId,
    al.Title AS AlbumTitle,
    t.TrackId,
    t.Name AS TrackName,
    t.MediaTypeId,
    t.GenreId,
    t.Composer,
    t.Milliseconds,  -- or: AS TrackMilliseconds, or even: AS TrackDuration,
    t.Bytes,
    t.UnitPrice
FROM Artist ar
JOIN Album al ON ar.ArtistId = al.ArtistId
JOIN Track t ON al.AlbumId = t.AlbumId
ORDER BY ar.Name, al.Title, t.Name
LIMIT 10;
```



## Q4: Titres doublons

Ecrivez une requête SQL pour identifier des artistes différents qui ont créé des morceaux portant exactement le même titre.

Le nom d'au moins une des artiste doit commencer par B.

La requête doit afficher :

- le nom de l’artiste 1 (artist1_name)
- le nom de l’artiste 2 (artist2_name)
- le titre du morceau commun (track_title)

Chaque combinaison d’artistes et de titre ne doit apparaître qu’une seule fois (pas de doublons inversés).

La solution de cette question est cachée. Rappel: même quand votre réponse est juste, l'interface reste rouge et affiche un message d'erreur.

```sql
SELECT
  -- c'est pas les bons champs, mais mieux pour debugger...
  ar1.ArtistId, ar1.Name, t1.TrackId, t1.Name,
  ar2.ArtistId, ar2.Name, t2.TrackId, t2.Name,

  ar1.Name AS artist1_name,
  ar2.Name AS artist2_name,
  t2.Name AS track_title

FROM Artist AS ar1
JOIN Album AS al1 ON ar1.ArtistId = al1.ArtistId
JOIN Track AS t1  ON al1.AlbumId = t1.AlbumId
JOIN Artist AS ar2
JOIN Album AS al2 ON ar2.ArtistId = al2.ArtistId
JOIN Track AS t2  ON al2.AlbumId = t2.AlbumId
WHERE t1.Name = t2.Name
  -- AND ar1.ArtistId <> ar2.ArtistId  -- la condition ci-dessous suffit
  AND ar1.ArtistId > ar2.ArtistId      -- permet d'éviter les doublons
  AND (ar1.Name LIKE 'B%' OR ar2.Name LIKE 'B%')
LIMIT 100;
```

| artist1_name                        | artist2_name        | track_title           |
| ----------------------------------- | ------------------- | --------------------- |
| Black Sabbath                       | Black Label Society | Snowblind             |
| Green Day                           | Black Sabbath       | Warning               |
| Creedence Clearwater Revival        | BackBeat            | Good Golly Miss Molly |
| Godsmack                            | Black Sabbath       | Changes               |
| Ozzy Osbourne                       | Black Label Society | No More Tears         |
| Ozzy Osbourne                       | Black Sabbath       | Black Sabbath         |
| Ozzy Osbourne                       | Black Sabbath       | N.I.B.                |
| Ozzy Osbourne                       | Black Label Society | Snowblind             |
| Ozzy Osbourne                       | Black Sabbath       | Snowblind             |
| Ozzy Osbourne                       | Black Sabbath       | The Wizard            |
| Pink Floyd                          | BackBeat            | Money                 |
| Stevie Ray Vaughan & Double Trouble | Buddy Guy           | Leave My Girl Alone   |
| Stevie Ray Vaughan & Double Trouble | Buddy Guy           | Let Me Love You Baby  |

\fi

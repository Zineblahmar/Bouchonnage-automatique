# Scénario 4 — Bouchonnage Automatique de Flacons sur Convoyeur (Smart Factory)

> **Projet :** Smart Factory — Poste de Bouchonnage  
> **Robot :** Dobot (pilotage via TCP — `DobotTCP`)  
> **Carte :** Arduino Uno (barrière + vérin)  
> **Langage :** Python 3 (liaison) / C++ Arduino (barrière-vérin)  
> **Bibliothèques :** `pyserial`, `DobotTCP`  
> **Statut :** ⏳ En intégration

---

# 📖 Présentation

Ce scénario constitue le **poste de bouchonnage** de la ligne de production **Smart Factory**.

Il intervient **juste après le poste de remplissage** : une fois le flacon rempli, il est déposé sur le **convoyeur**, transporté jusqu'au poste de bouchonnage, puis **immobilisé avec précision** devant le bras **Dobot** afin que celui-ci puisse saisir un bouchon et le visser sur le flacon.

L'objectif de ce positionnement précis est d'éliminer les imprécisions liées au remplissage : le flacon peut arriver avec un léger décalage sur le convoyeur, la barrière et le vérin servent donc à **détecter, cadencer et bloquer** chaque flacon toujours à la même position avant l'intervention du robot.

Le système est composé de **deux sous-systèmes synchronisés** :

1. **Arduino** — gère la détection du flacon, la barrière d'entrée (anti-collision entre flacons) et le vérin de blocage/positionnement.
2. **Python + Dobot** — reçoit le signal de l'Arduino, exécute la séquence de prise du bouchon et de vissage, puis renvoie un signal de fin de cycle.

---

# 📍 Conditions de fonctionnement

- Le flacon est déjà rempli lorsqu'il arrive sur le convoyeur (poste de remplissage en amont).
- Un seul flacon est traité à la fois devant le vérin ; la barrière sert à réguler l'arrivée des flacons suivants.
- **4 positions de bouchon** sont préprogrammées (`POSES_BOUCHONS`) et utilisées **à tour de rôle** à chaque cycle. Les bouchons doivent être réapprovisionnés à ces emplacements fixes.
- La position du flacon devant le Dobot est supposée **fixe et répétable**, garantie par le blocage mécanique du vérin.
- Toute modification de la géométrie du poste (position du convoyeur, hauteur du vérin, position des bouchons) nécessite une remise à jour des coordonnées dans le code.

---

# 🎯 Objectifs du scénario

- ✔ Détection fiable de l'arrivée d'un flacon (capteur infrarouge)
- ✔ Régulation du flux de flacons via une barrière servomotorisée
- ✔ Blocage / positionnement précis du flacon via un vérin électrique
- ✔ Synchronisation Arduino ⇄ Python par liaison série
- ✔ Prise automatique d'un bouchon par ventouse (Dobot)
- ✔ Vissage automatique du bouchon sur le flacon
- ✔ Retour du vérin et réarmement automatique du poste pour le flacon suivant

---

# 🏗️ Principe de Fonctionnement

Le poste repose sur trois éléments principaux.

## 🧠 Arduino Uno

Gère en autonomie la partie mécanique amont :

- lecture du capteur infrarouge (détection flacon) ;
- pilotage du servomoteur de la barrière ;
- pilotage du moteur DC du vérin via un pont en H **L298N** ;
- envoi du signal `START_PYTHON` et attente du signal `PYTHON_DONE`.

## 💻 PC (script `NAYL_arduino_link.py`)

- écoute en continu le port série de l'Arduino ;
- déclenche la séquence Dobot dès réception de `START_PYTHON` ;
- renvoie `PYTHON_DONE` une fois le bouchon vissé, pour que l'Arduino rentre le vérin.

## 🤖 Bras Dobot

- va chercher un bouchon (position tournante parmi 4 postes) ;
- l'aspire avec sa ventouse (`SetSucker`) ;
- le dépose sur le flacon en plusieurs paliers de descente ;
- effectue une rotation de l'outil pour simuler le vissage ;
- relâche la ventouse puis retourne en position `Home` / caméra.

---

# 🔄 Déroulement du scénario

```text
                     HOME (Arduino pret)
                            │
                            ▼
                Detection flacon (capteur IR)
                            │
                            ▼
                Confirmation anti-parasite (5 lectures)
                            │
                            ▼
                  Ouverture de la barriere
                            │
                            ▼
                  Fermeture de la barriere
                            │
                            ▼
        Delai calibre -> le flacon arrive devant le verin
                            │
                            ▼
                  Sortie du verin (blocage/positionnement)
                            │
                            ▼
              Envoi "START_PYTHON" vers le PC
                            │
                            ▼
        Dobot : approche bouchon -> ventouse ON -> transport
                            │
                            ▼
        Dobot : descente palier par palier sur le flacon
                            │
                            ▼
              Dobot : rotation outil (vissage)
                            │
                            ▼
              Dobot : ventouse OFF -> retour Home/camera
                            │
                            ▼
              Envoi "PYTHON_DONE" vers l'Arduino
                            │
                            ▼
                  Rentree du verin
                            │
                            ▼
              Rearmement -> pret pour le flacon suivant
```

---

# 📍 Séquence détaillée

| Étape | Acteur | Action | Description |
|-------|--------|--------|-------------|
| 1 | Arduino | Veille | Capteur IR surveillé en continu |
| 2 | Arduino | Détection | Flacon détecté + confirmation sur 5 lectures (anti-bruit) |
| 3 | Arduino | Barrière ouverte | Laisse passer le flacon en cours, bloque le suivant |
| 4 | Arduino | Barrière fermée | Se referme immédiatement après ouverture (~1 s) |
| 5 | Arduino | Temporisation calibrée | Attente jusqu'à `TEMPS_ARRIVEE_VERIN_MS` (3396 ms) depuis le début de l'ouverture |
| 6 | Arduino | Sortie vérin | Le vérin sort (4,5 s) pour bloquer/positionner le flacon devant le poste Dobot |
| 7 | Arduino → PC | Signal | Envoi de `START_PYTHON` sur le port série |
| 8 | Python/Dobot | Approche bouchon | Retour position caméra puis déplacement vers le poste de bouchon courant |
| 9 | Python/Dobot | Prise | Activation ventouse (`SetSucker(1)`), attente stabilisation |
| 10 | Python/Dobot | Transport | Retour position caméra → `Home` → position flacon |
| 11 | Python/Dobot | Dépose / vissage | Descente en plusieurs paliers + rotation de l'outil |
| 12 | Python/Dobot | Relâche | Désactivation ventouse (`SetSucker(0)`), remontée, retour `Home`/caméra |
| 13 | PC → Arduino | Signal | Envoi de `PYTHON_DONE` sur le port série |
| 14 | Arduino | Rentrée vérin | Le vérin rentre (4,5 s) |
| 15 | Arduino | Réarmement | Courte pause (300 ms) puis nouveau cycle possible |

---

# ⏱️ Paramètres de synchronisation (Arduino)

| Paramètre | Valeur | Rôle |
|-----------|--------|------|
| `TEMPS_ARRIVEE_VERIN_MS` | 3396 ms | Délai entre le début d'ouverture de la barrière et l'arrivée du flacon devant le vérin |
| Durée sortie vérin | 4500 ms | Temps de sortie de tige pour bloquer le flacon |
| Durée rentrée vérin | 4500 ms | Temps de rentrée de tige après signal `PYTHON_DONE` |
| Timeout attente Python | 120 000 ms | Sécurité si le PC ne répond pas |
| Confirmation détection | 5 lectures × 20 ms | Filtre anti-parasite du capteur IR |

---

# ⚙️ Algorithme du scénario

```text
Debut (Arduino)
↓
Lecture capteur IR
↓
Si flacon detecte ET confirme
↓
Ouvrir barriere -> attendre 1 s -> fermer barriere
↓
Attendre jusqu'a 3396 ms depuis le debut d'ouverture
↓
Sortir le verin (bloquer le flacon)
↓
Envoyer "START_PYTHON"
↓
Attendre "PYTHON_DONE" (max 120 s)
    ↓
    (cote Python/Dobot)
    Aller au poste bouchon courant
    ↓
    Activer ventouse
    ↓
    Transporter le bouchon vers le flacon
    ↓
    Descendre par paliers + visser (rotation outil)
    ↓
    Desactiver ventouse
    ↓
    Retour Home / camera
    ↓
    Envoyer "PYTHON_DONE"
↓
Rentrer le verin
↓
Rearmer le systeme
↓
Fin de cycle -> retour en veille
```

---

# 🛠️ Technologies utilisées

## Matériel

| Équipement | Description |
|------------|-------------|
| Dobot (TCP) | Bras robotisé pour la prise et le vissage du bouchon |
| Arduino Uno | Pilotage de la barrière, du vérin et de la synchronisation |
| Capteur infrarouge | Détection de l'arrivée d'un flacon |
| Servomoteur (barrière) | Ouverture / fermeture de la barrière d'entrée |
| Moteur DC + pont en H L298N | Actionnement du vérin de blocage/positionnement |
| Convoyeur | Transport des flacons remplis depuis le poste de remplissage |
| Ventouse pneumatique (Dobot) | Préhension des bouchons |
| Flacons / Bouchons | Consommables du poste |

## Logiciel

| Logiciel / Bibliothèque | Utilisation |
|--------------------------|-------------|
| Arduino IDE | Programmation de la carte (`barriere_verin.ino`) |
| Python 3 | Script de liaison Arduino ↔ Dobot (`NAYL_arduino_link.py`) |
| `pyserial` | Communication série avec l'Arduino |
| `DobotTCP` | Pilotage du bras Dobot via TCP |

---

# 🔌 Câblage (Arduino)

| Broche | Fonction |
|--------|----------|
| D4 | Capteur infrarouge (`INPUT_PULLUP`) |
| D5 | Servomoteur de la barrière |
| D9 (ENA) | Vitesse moteur du vérin (PWM) |
| D8 (IN1) | Sens moteur du vérin |
| D7 (IN2) | Sens moteur du vérin |

---

# 📂 Structure du dossier

```text
scenario_4_bouchonnage_convoyeur/
│
├── barriere_verin.ino         # Programme Arduino : barrière + vérin + synchronisation série
├── NAYL_arduino_link.py       # Script Python : liaison série Arduino <-> pilotage Dobot
└── README.md
```

---

# ▶️ Exécution

## 1. Téléverser le programme Arduino

- Ouvrir `barriere_verin.ino` dans l'Arduino IDE.
- Sélectionner la bonne carte / le bon port.
- Téléverser le programme.

## 2. Configurer le script Python

Dans `NAYL_arduino_link.py`, adapter si besoin :

```python
SERIAL_PORT = "COM7"       # port série de l'Arduino
BAUD_RATE = 9600
DOBOT_IP = "192.168.5.1"
DOBOT_PORT = 29999
```

## 3. Lancer la liaison

```bash
python NAYL_arduino_link.py
```

Le script se connecte à l'Arduino puis au Dobot, exécute `Home()`, et attend ensuite en continu les signaux `START_PYTHON`.

## 4. Démarrer le convoyeur

Une fois le poste initialisé (message `[DOBOT] Robot pret.`), démarrer le convoyeur : chaque flacon détecté par le capteur IR déclenche automatiquement un cycle complet de bouchonnage.

---

# ✅ Résultat attendu

À la fin d'un cycle :

- le flacon a été bloqué avec précision devant le poste Dobot ;
- un bouchon a été saisi puis vissé sur le flacon ;
- le vérin est rentré et la barrière est réarmée ;
- le poste est prêt à traiter le flacon suivant sans intervention manuelle.

---

# 📌 État du développement

| Fonction | État |
|----------|------|
| Détection flacon (IR) | ✅ Fonctionnel |
| Barrière servomotorisée | ✅ Fonctionnel |
| Vérin de blocage/positionnement | ✅ Fonctionnel |
| Synchronisation série Arduino ↔ Python | ✅ Fonctionnel |
| Séquence de prise et vissage (Dobot) | ⏳ En cours de validation |
| Intégration complète sur convoyeur réel | ⏳ En attente de tests |

---

# 🔧 Dépannage

| Problème | Cause possible | Solution |
|----------|----------------|----------|
| L'Arduino ne détecte jamais de flacon | Capteur IR mal réglé ou mal câblé | Vérifier le câblage D4 et la sensibilité du capteur |
| Le flacon n'est pas bien positionné devant le Dobot | `TEMPS_ARRIVEE_VERIN_MS` mal calibré | Réajuster la constante selon la vitesse réelle du convoyeur |
| Le vérin ne sort / ne rentre pas | Mauvais câblage du L298N ou alimentation insuffisante | Vérifier ENA/IN1/IN2 et l'alimentation moteur |
| `Timeout Python` affiché côté Arduino | Le script Python n'est pas lancé ou le Dobot est bloqué | Vérifier que `NAYL_arduino_link.py` tourne et que le Dobot répond |
| Le bouchon n'est pas aspiré | Mauvaise pression de la ventouse ou position mal calibrée | Vérifier la pompe à vide et recalibrer la pose du bouchon |
| Erreur de connexion série Python | Mauvais `SERIAL_PORT` ou port déjà occupé | Vérifier le port dans le Gestionnaire de périphériques / `ls /dev/tty*` |

---

# ⚠️ Avertissements

- ⚠️ Ne jamais placer les mains devant la barrière ou le vérin pendant le fonctionnement du convoyeur.
- ⚠️ Toujours vérifier que la zone de travail du Dobot est libre avant de démarrer le convoyeur.
- ⚠️ Ne pas modifier `TEMPS_ARRIVEE_VERIN_MS` sans re-tester la synchronisation complète du poste.
- ⚠️ Couper l'alimentation avant toute intervention sur le câblage (capteur, servomoteur, L298N).
- ⚠️ Prévoir un arrêt d'urgence facilement accessible pendant les essais.

---

# 💡 Bonnes pratiques

- Tester séparément le sous-système Arduino (barrière + vérin) et le sous-système Dobot avant l'intégration complète.
- Recalibrer `TEMPS_ARRIVEE_VERIN_MS` après tout changement de vitesse du convoyeur.
- Vérifier régulièrement l'alignement des 4 postes de bouchons (`POSES_BOUCHONS`).
- Conserver un journal des cycles (succès / échecs) pour mesurer le taux de réussite du poste.
- Toujours terminer un cycle de test par un retour `Home` du Dobot avant d'arrêter le programme.

---

**Projet :** Smart Factory — Poste de Bouchonnage  
**Version :** 1.0  
**Dernière mise à jour :** 13 Août 2026

# 🏗️ Architecture Technique — Poste de Bouchonnage Smart Factory

> **Version :** 1.0  
> **Projet :** projet-robotique-fin-annee  
> **Date de mise à jour :** 13 Août 2026  
> **Statut :** ⏳ En intégration

---

# 📖 Présentation

Ce document décrit l'architecture matérielle et logicielle du **poste de bouchonnage automatique** de la ligne **Smart Factory**.

Il explique comment les différents composants (convoyeur, capteur, Arduino, PC, bras Dobot) communiquent entre eux afin de détecter un flacon rempli, le positionner avec précision, puis le boucher automatiquement.

L'objectif est de fournir une vue globale du fonctionnement du système ainsi que des mécanismes de synchronisation et de sécurité intégrés.

---

# 🏛️ Architecture Générale

## Vue d'ensemble

```text
┌───────────────────┐
│  Poste de          │
│  remplissage        │
│  (en amont)         │
└─────────┬───────────┘
          │  flacon rempli depose sur le convoyeur
          ▼
┌───────────────────────────────────────────────────────────┐
│                        Convoyeur                            │
└─────────┬────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────┐        Port série USB        ┌───────────────────────────┐
│        Arduino Uno         │ ───────────────────────────► │           PC               │
│  (barriere_verin.ino)      │  "START_PYTHON"               │  (NAYL_arduino_link.py)    │
│                            │ ◄─────────────────────────── │                             │
│  - Capteur IR (D4)         │  "PYTHON_DONE"                 └──────────────┬──────────────┘
│  - Servo barriere (D5)     │                                                │
│  - Verin via L298N         │                                                │  TCP/IP
│    (ENA=D9, IN1=D8, IN2=D7)│                                                │  192.168.5.1:29999
└───────────────────────────┘                                                ▼
                                                                ┌───────────────────────────┐
                                                                │        Bras Dobot          │
                                                                │  (prehension + vissage)    │
                                                                │      Ventouse pneumatique  │
                                                                └───────────────────────────┘
```

---

# 🔄 Flux de Fonctionnement

Le fonctionnement général du système est le suivant :

1. Le flacon rempli est déposé sur le **convoyeur** par le poste de remplissage en amont.
2. Le **capteur infrarouge** (Arduino, broche D4) détecte l'arrivée du flacon.
3. L'**Arduino** ouvre puis referme la **barrière** (servomoteur, broche D5) pour réguler le flux de flacons.
4. Après un délai calibré (`TEMPS_ARRIVEE_VERIN_MS`), l'Arduino sort le **vérin** (moteur DC piloté par le pont en H **L298N**) afin de bloquer/positionner précisément le flacon devant le poste Dobot.
5. L'Arduino envoie le message `START_PYTHON` au **PC** via la **liaison série USB**.
6. Le script Python (`NAYL_arduino_link.py`) reçoit ce message et déclenche la séquence du **bras Dobot** via une connexion **TCP/IP**.
7. Le Dobot va chercher un bouchon, l'aspire avec sa **ventouse pneumatique**, le transporte et le **visse** sur le flacon.
8. Une fois le vissage terminé, le PC renvoie `PYTHON_DONE` à l'Arduino.
9. L'Arduino **rentre le vérin**, réarme le système et se remet en veille pour le flacon suivant.

---

# 🧩 Architecture Logicielle

```text
        barriere_verin.ino                    NAYL_arduino_link.py
                │                                       │
                ▼                                       ▼
      Boucle loop() Arduino                     Boucle d'ecoute serie
   (capteur, barriere, verin)                  (pyserial + threading)
                │                                       │
                └──────────── Port série USB ───────────┘
                          "START_PYTHON" / "PYTHON_DONE"
                                        │
                                        ▼
                              Bibliothèque DobotTCP
                                        │
                                        ▼
                              API de contrôle du robot
                             (MovJ, SetSucker, Home...)
                                        │
                                        ▼
                                Bras Dobot (TCP/IP)
```

Le poste repose sur **deux programmes indépendants et synchronisés** :

- **`barriere_verin.ino`** (Arduino) : gère en autonomie la mécanique amont (détection, barrière, vérin) et communique par messages texte sur le port série.
- **`NAYL_arduino_link.py`** (PC) : fait le pont entre l'Arduino et le Dobot ; il reste connecté en permanence au robot (pas de reconnexion à chaque flacon) et pilote la séquence de prise/vissage via `DobotTCP`.

---

# 🔧 Composants Matériels

| Composant | Type | Rôle |
|-----------|------|------|
| **Convoyeur** | Transporteur | Achemine les flacons remplis depuis le poste de remplissage |
| **Capteur infrarouge** | Capteur | Détecte l'arrivée d'un flacon devant le poste |
| **Arduino Uno** | Microcontrôleur | Pilote la barrière et le vérin, synchronise avec le PC |
| **Servomoteur** | Actionneur | Ouvre/ferme la barrière de régulation des flacons |
| **Moteur DC + L298N** | Actionneur | Sort/rentre le vérin de blocage et de positionnement |
| **PC** | Ordinateur | Exécute le script de liaison et pilote le Dobot |
| **Bras Dobot** | Robot 4/6 axes | Saisit le bouchon et le visse sur le flacon |
| **Ventouse pneumatique** | Effecteur | Préhension du bouchon (`SetSucker`) |

---

# 🔌 Connexions Physiques

## Communication Arduino ↔ PC

| Paramètre | Valeur |
|-----------|--------|
| Type de liaison | Série USB |
| Port | `COM7` (Windows) — à adapter (`/dev/ttyUSB0` sous Linux) |
| Vitesse | **9600 bauds** |
| Messages échangés | `START_PYTHON` (Arduino → PC), `PYTHON_DONE` (PC → Arduino) |

## Communication PC ↔ Dobot

| Paramètre | Valeur |
|-----------|--------|
| Type de liaison | TCP/IP |
| Adresse IP | `192.168.5.1` |
| Port | `29999` |
| Bibliothèque | `DobotTCP` |

## Câblage Arduino (barrière + vérin)

| Broche | Nom | Fonction |
|--------|-----|----------|
| D4 | `IR_SENSOR` | Capteur infrarouge (entrée, `INPUT_PULLUP`) |
| D5 | `SERVO_PIN` | Servomoteur de la barrière |
| D9 | `ENA` | Vitesse du moteur du vérin (PWM, L298N) |
| D8 | `IN1` | Sens de rotation du moteur du vérin |
| D7 | `IN2` | Sens de rotation du moteur du vérin |

### Schéma simplifié

```text
                Arduino Uno
           ┌───────────────────┐
           │                   │
  IR ──────┤ D4                │
           │                   │
Servo ─────┤ D5                │
 (barriere)│                   │
           │              D9 ──┼──► ENA  (L298N)
           │              D8 ──┼──► IN1  (L298N)
           │              D7 ──┼──► IN2  (L298N)
           │                   │
           └───────────────────┘
                                     │
                                     ▼
                              Moteur DC (verin)
```

> **Remarque :** le sens de sortie/rentrée du vérin est déterminé par la combinaison `IN1`/`IN2` (`moteurAvant()` / `moteurArriere()`), la vitesse étant fixée au maximum (`analogWrite(ENA, 255)`).

---

# 🛡️ Sécurité du Système

## 1. Anti-rebond / anti-parasite

La détection du capteur infrarouge est **confirmée sur 5 lectures consécutives** (`detectionConfirmee()`) avant de déclencher un cycle, afin d'éviter qu'un parasite électrique ne lance une séquence intempestive.

## 2. Timeout de synchronisation

Si le PC ne répond pas dans un délai de **120 secondes** après l'envoi de `START_PYTHON`, l'Arduino affiche `Timeout Python` et poursuit la fin de son cycle (rentrée du vérin), évitant un blocage définitif du poste.

## 3. Cadencement calibré

Le délai `TEMPS_ARRIVEE_VERIN_MS` (3396 ms) garantit que le vérin ne sort **qu'une fois le flacon réellement arrivé** devant lui, évitant tout choc prématuré.

## 4. Arrêt d'urgence (côté Python/Dobot)

En cas de :

- interruption clavier (`Ctrl + C`) ;
- erreur Python ;
- exception inattendue,

le script :

- tente d'exécuter `robot.ClearError()` puis `robot.Disconnect()` proprement ;
- ferme le port série de l'Arduino.

---

# 📂 Organisation du Projet

```text
projet-robotique-fin-annee/
│
├── docs/
│   └── architecture.md
│
├── src/
│   │
│   └── scenario_4_bouchonnage_convoyeur/
│       ├── barriere_verin.ino
│       ├── NAYL_arduino_link.py
│       └── README.md
│
└── README.md
```

---

# 📋 Liste des Scénarios Embarqués

| N° | Scénario | Dossier | Statut |
|----|----------|---------|--------|
| 4 | Bouchonnage automatique de flacons sur convoyeur | `src/scenario_4_bouchonnage_convoyeur/` | ⏳ En intégration |

---

# ✅ Résumé

L'architecture du poste de bouchonnage repose sur une séparation claire entre :

- **L'Arduino Uno**, chargé de la mécanique amont (détection, barrière, positionnement par vérin) ;
- **Le PC**, qui fait le pont entre l'Arduino et le Dobot ;
- **Le bras Dobot**, chargé exclusivement de la prise et du vissage du bouchon.

Cette architecture modulaire, basée sur une synchronisation par simples messages texte sur liaison série, facilite :

- l'ajout de nouveaux postes sur la même ligne (contrôle qualité, étiquetage...) ;
- la maintenance indépendante de chaque sous-système ;
- l'évolution vers une détection par vision artificielle ou un pilotage par PLC industriel.

---

**Document :** `docs/architecture.md`

**Version :** 1.0

**Dernière mise à jour :** 13 Août 2026

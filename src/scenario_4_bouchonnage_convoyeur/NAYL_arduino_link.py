"""
Script de liaison Arduino <-> Dobot
------------------------------------
- Ecoute en continu le port série de l'Arduino.
- Quand l'Arduino envoie "START_PYTHON", lance la séquence de vissage du Dobot.
- Une fois la séquence terminée, renvoie "PYTHON_DONE" à l'Arduino
  pour qu'il rentre le vérin et termine son cycle.
- Le robot Dobot reste connecté en permanence (pas de reconnexion à chaque flacon).
"""

import time
import serial
from DobotTCP import Dobot

# ======================================================
# CONFIGURATION - A ADAPTER
# ======================================================
SERIAL_PORT = "COM7"      # ex: "COM5" sous Windows, "/dev/ttyUSB0" sous Linux
BAUD_RATE = 9600           # doit correspondre à Serial.begin(9600) sur l'Arduino
DOBOT_IP = "192.168.5.1"
DOBOT_PORT = 29999

# Nombre de flacons attendus avant de couper le programme (5 dans ton script d'origine)
# Mets None pour tourner indéfiniment
NB_FLACONS_MAX = None


def sequence_bouchon(robot, pose_bouchon):
    """
    Effectue la prise d'un bouchon + vissage sur la bouteille.
    pose_bouchon : chaîne de pose pour aller chercher le bouchon.
    """
    # Retour position caméra / sécurité
    robot.MovJ("pose={-63.19, -310.82, 323.5, -179.04, 1.07, -95.82}")
    time.sleep(2)

    # Aller chercher le bouchon
    robot.MovJ(f"pose={{{pose_bouchon}}}")
    time.sleep(4)

    # Pompe ON (prise du bouchon)
    robot.SetSucker(1)
    time.sleep(10)

    # Retour position caméra
    robot.MovJ("pose={-63.19, -310.82, 323.5, -179.04, 1.07, -95.82}")
    time.sleep(2)
    robot.Home()
    time.sleep(2)

    # Position de la bouteille
    robot.MovJ("pose={-324.65, 61.98, 34, -179.67, -0.65, 81.46}")
    time.sleep(2)
    #robot.MovJ("pose={-328.55, 94.59 , 33, -179.10, -0.25, 80.50}")
    #time.sleep(2)
    #robot.MovJ("pose={-328.5, 94.59, 32.4, -179.10, -0.25, 80.50}")
    #time.sleep(2)
    robot.MovJ("pose={-324.65, 61.98, 32, -179.67, -0.65, 81.46}")
#presionner le bouchons
    #robot.MovJ("pose={-328.55, 96.73, 30, -179.10, -0.25, 80.50}")
    #time.sleep(3)
    #robot.MovJ("pose={-328.55, 96.73, 28, -179.10, -0.25, 80.50}")
    #time.sleep(3)   
    robot.MovJ("pose={-324.65, 61.98, 27, -179.67, -0.65, 81.46}")
    time.sleep(1)
    #robot.MovJ("pose={-328.55, 96.73, 26, -179.10, -0.25, 80.50}")
    #time.sleep(3)
    robot.MovJ("pose={-324.65, 61.98, 25.5, -179.67, -0.65, 81.46}")
    time.sleep(1)
    robot.MovJ("pose={-324.65, 61.98, 24, -179.67, -0.65, 81.46}")
    time.sleep(1)
#la desentesur la bouteille
    robot.MovJ("pose={-324.65, 61.98, 23.62, -179.67, -0.65, 81.46}")
    time.sleep(1)
    #robot.MovJ("pose={-321.78, 74.44, 23, -179.10, -0.25, 80.50}")
    time.sleep(1)
    robot.MovJ("pose={-324.65, 61.98, 22, -179.67, -0.65, 81.46}")
#deuxiéme pressionner
    robot.MovJ("pose={-324.65, 61.98, 21.5, -179.67, -0.65, 81.46}")
    time.sleep(1)
#troisiéme pressionner
    robot.MovJ("pose={-324.65, 61.98, 19, -179.67, -0.65, 81.46}")
    #time.sleep(3)
#rotation pour le vissage
    robot.MovJ("pose={-324.65, 61.98, 19,179.69, 0.45, 48.69 }")
    time.sleep(1)
#vissage final  
    robot.MovJ("pose={-324.65, 61.98, 19,179.13, -0.113, 30.50}")
    time.sleep(3)
    robot.SetSucker(0)
    time.sleep(7)
    robot.MovJ("pose={-324.65, 61.98, 18,179.13, -0.113, 30.50}")
    time.sleep(3)
#haut de la bouteille
    robot.MovJ("pose={-324.65, 61.98, 32,179.13, -0.113, 30.50}")
    time.sleep(2)
    robot.MovJ("pose={-324.65, 61.98, 40,179.13, -0.113, 30.50}")
    time.sleep(3)
    # Retour home puis caméra
    robot.Home()
    time.sleep(2)
    robot.MovJ("pose={-63.19, -310.82, 323.5, -179.04, 1.07, -95.82}")
    time.sleep(2)


# Liste des positions des bouchons, dans l'ordre (adapte selon ton besoin réel)
POSES_BOUCHONS = [
    "32.02, -428.57, 35, 174.78, -1.70, -151.84",
    "28.90, -393.05,35 , 175.12, 4.75, -100.27",
    "-5.11, -428.29, 35, 173.37, 2.67, -105.09",
    "-1.75, -398.3, 35, 172.39, 5.93, -104.29",
]


def run_robot_sequence(robot, cycle_index):
    """
    Lance la séquence complète pour UN flacon (déclenchée par un signal START_PYTHON).
    cycle_index : numéro du cycle (0, 1, 2, ...) pour choisir la bonne pose de bouchon.
    """
    pose = POSES_BOUCHONS[cycle_index % len(POSES_BOUCHONS)]
    print(f"[ROBOT] Debut sequence bouchon #{cycle_index + 1}")
    sequence_bouchon(robot, pose)
    print(f"[ROBOT] Fin sequence bouchon #{cycle_index + 1}")


def main():
    # --- Connexion à l'Arduino ---
    print(f"[SERIE] Connexion au port {SERIAL_PORT} ...")
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # laisser le temps à l'Arduino de redémarrer après ouverture du port
    print("[SERIE] Connecte.")

    # --- Connexion au Dobot (une seule fois) ---
    print("[DOBOT] Connexion au robot ...")
    robot = Dobot(ip=DOBOT_IP, port=DOBOT_PORT)
    robot.Connect()
    robot.EnableRobot()
    robot.Home()
    time.sleep(2)
    print("[DOBOT] Robot pret.")

    cycle_index = 0

    try:
        while True:
            if NB_FLACONS_MAX is not None and cycle_index >= NB_FLACONS_MAX:
                print("[MAIN] Nombre max de flacons atteint, arret.")
                break

            if arduino.in_waiting > 0:
                ligne = arduino.readline().decode("utf-8", errors="ignore").strip()
                if not ligne:
                    continue

                print(f"[ARDUINO] {ligne}")

                if ligne == "START_PYTHON":
                    # Lancer la séquence du robot pour ce flacon
                    run_robot_sequence(robot, cycle_index)
                    cycle_index += 1

                    # Prévenir l'Arduino que c'est terminé
                    arduino.write(b"PYTHON_DONE\n")
                    print("[SERIE] PYTHON_DONE envoye a l'Arduino.")

            time.sleep(0.05)  # petite pause pour ne pas saturer le CPU

    except KeyboardInterrupt:
        print("[MAIN] Interruption manuelle.")

    finally:
        print("[DOBOT] Deconnexion du robot ...")
        try:
            robot.ClearError()
            robot.Disconnect()
        except Exception as e:
            print(f"[DOBOT] Erreur a la deconnexion: {e}")

        arduino.close()
        print("[SERIE] Port ferme. Fin du programme.")


if __name__ == "__main__":
    main()

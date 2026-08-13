#include <Servo.h>

//----------------------
// Broches
//----------------------
#define IR_SENSOR 4
#define SERVO_PIN 5

// L298N
#define ENA 9
#define IN1 8
#define IN2 7

// Angles de la barrière
#define ANGLE_OUVERT 0
#define ANGLE_FERME  180

// Temps exact mesuré entre le début d'ouverture de la barrière
// et l'arrivée du flacon devant le vérin (à ajuster si besoin)
#define TEMPS_ARRIVEE_VERIN_MS 3396

Servo barriere;

bool cycleEnCours = false;

void setup() {
  Serial.begin(9600);

  pinMode(IR_SENSOR, INPUT_PULLUP); // évite les lectures flottantes/parasites
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  barriere.attach(SERVO_PIN);

  // Position initiale : fermée
  barriere.write(ANGLE_FERME);
  moteurStop();

  Serial.println("Systeme pret");
}

void loop() {
  if (digitalRead(IR_SENSOR) == LOW && !cycleEnCours) {

    // Confirmation de détection (anti faux-positif / bruit électrique)
    if (!detectionConfirmee()) {
      return;
    }

    cycleEnCours = true;
    Serial.println("Objet detecte");

    //=========================
    // 1. Ouvrir la barrière
    //=========================
    // On démarre le chrono ICI : c'est le point de référence des 3.90 s
    unsigned long tBarriereStart = millis();

    Serial.println("Ouverture barriere");
    ouvrirBarriere();
    delay(1000);

    //=========================
    // 2. Fermer la barrière
    //=========================
    Serial.println("Fermeture barriere");
    fermerBarriere();

    //=========================
    // 2bis. Ajustement pour arriver exactement à 3.90 s
    //=========================
    unsigned long elapsed = millis() - tBarriereStart;
    if (elapsed < TEMPS_ARRIVEE_VERIN_MS) {
      delay(TEMPS_ARRIVEE_VERIN_MS - elapsed);
    }
    // Si jamais le mouvement servo a déjà pris plus de 3.90 s,
    // on ne délaye pas davantage (on est déjà en retard).

    //=========================
    // 3. Sortir le vérin
    //=========================
    Serial.println("Sortie verin");
    moteurAvant();
    delay(4500);
    moteurStop();

    //=========================
    // 4. Signal Python + attente réponse
    //=========================
    Serial.println("START_PYTHON");

    unsigned long startWait = millis();
    bool pythonDone = false;

    while (millis() - startWait < 120000) {
      if (Serial.available() > 0) {
        String msg = Serial.readStringUntil('\n');
        msg.trim();
        if (msg == "PYTHON_DONE") {
          pythonDone = true;
          break;
        }
      }
      delay(100);
    }

    if (!pythonDone) {
      Serial.println("Timeout Python");
    }

    //=========================
    // 5. Rentrer le vérin
    //=========================
    Serial.println("Rentree verin");
    moteurArriere();
    delay(4500);
    moteurStop();

    Serial.println("Cycle termine");

    // On ne bloque plus en attendant que le capteur se libère :
    // un flacon suivant peut déjà être en attente devant la barrière
    // (capteur toujours LOW). On réarme directement pour que le
    // loop() puisse relancer immédiatement un nouveau cycle si besoin.
    delay(300); // courte pause mécanique avant de réarmer
    cycleEnCours = false;
  }
}

//------------------------------------
// Confirme la détection sur plusieurs lectures
// (évite qu'un parasite électrique déclenche le cycle)
//------------------------------------
bool detectionConfirmee() {
  for (int i = 0; i < 5; i++) {
    if (digitalRead(IR_SENSOR) != LOW) {
      return false;
    }
    delay(20);
  }
  return true;
}

//------------------------------------
// Ouvrir la barrière
//------------------------------------
void ouvrirBarriere() {
  int posActuelle = barriere.read();
  for (int pos = posActuelle; pos >= ANGLE_OUVERT; pos--) {
    barriere.write(pos);
    delay(8);
  }
}

//------------------------------------
// Fermer la barrière
//------------------------------------
void fermerBarriere() {
  int posActuelle = barriere.read();
  for (int pos = posActuelle; pos <= ANGLE_FERME; pos++) {
    barriere.write(pos);
    delay(8);
  }
}

//------------------------------------
// Vérin SORT
//------------------------------------
void moteurAvant() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, 255);
}

//------------------------------------
// Vérin RENTRE
//------------------------------------
void moteurArriere() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 255);
}

//------------------------------------
// Arrêt du moteur
//------------------------------------
void moteurStop() {
  analogWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

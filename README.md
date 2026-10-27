# Don't Blink

A webcam-only interactive computer vision game controlled entirely by body and hand gestures. No keyboard or mouse. Survive 3 intense stages or face GAME OVER! Inspired by Squid Game.

Built with Python, OpenCV, and MediaPipe.

## Stages

1. Don't Move: Green light means move, red light means freeze. Any motion detected during red light eliminates the player (motion detection).
2. Trace: A shape appears on screen and the player traces it in the air with a finger. The system compares the drawn path with the shape (MediaPipe hand tracking, air canvas, shape matching).
3. Lock & Fire: The hand becomes a gun. The index finger aims, the thumb fires, and random targets appear on screen (MediaPipe hand tracking and gesture recognition).

## Tech Stack

- Python
- OpenCV
- MediaPipe
- NumPy
- pygame (music and sound effects)

## Requirements

- A computer with a webcam
- Good lighting
- Python 3.13 (the version used in development)

## How to Run

pip install -r requirements.txt
python main.py
To run a single stage on its own:

python run_stage1.py
python run_stage2.py
python run_stage3.py
## Project Structure

Don-t-Blink/
├── main.py            # Game entry point
├── ui.py              # Screens and interface
├── stages/            # The three game stages
├── trace/             # Hand path tracking and shape loading (stage 2)
├── assest/traces/     # Shape images used in the trace stage
├── docs/              # Full project report
└── requirements.txt
## Documentation

The full project report is available in the [docs/](docs) folder.

## Team

Computer Vision course project, Robotics Club, 2026.

- Namaa Muhammad Osama Mustafa
- Aya Firas Al-Hayek
- Tuqa Muhammad Al-Khatib
- Sara Salloum

Coaches: Eng. Yaman Tahseen, Eng. Alaa Habbobati

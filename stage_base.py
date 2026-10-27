"""The contract every stage follows. Do NOT change it without telling the team.

update(frame, dt):
  - frame: current camera image (mirrored, size config.W x config.H). Draw on it directly.
  - dt: seconds since the last frame.
  - return RUNNING, WIN or LOSE.
The time limit is handled by the game (when time is up the stage is lost).
"""

RUNNING = "RUNNING"
WIN = "WIN"
LOSE = "LOSE"


class Stage:
    name = "Stage"
    description = ""
    time_limit = 60

    def start(self):
        """Called once when the stage begins. Create trackers/state here."""

    def update(self, frame, dt):
        return RUNNING

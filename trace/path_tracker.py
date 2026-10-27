import numpy as np


class PathTracker:
    """Follows the fingertip along the outline.
    - points close to the finger (mark_tol) become 'visited'  -> progress
    - the finger is 'on the line' if it is within fail_tol of the outline
    """

    def __init__(self, path, mark_tol=22, fail_tol=45):
        self.path = np.asarray(path, dtype=float)
        self.mark_tol = mark_tol
        self.fail_tol = fail_tol
        self.visited = np.zeros(len(self.path), dtype=bool)
        self.distance = None        # distance from the finger to the outline
        self.on_path = False

    def update(self, point):
        d = np.hypot(self.path[:, 0] - point[0], self.path[:, 1] - point[1])
        self.distance = float(d.min())
        self.on_path = self.distance <= self.fail_tol
        self.visited[d <= self.mark_tol] = True
        return self.on_path

    def touching(self):
        """True if the finger is really on the line (used to start the stage)."""
        return self.distance is not None and self.distance <= self.mark_tol

    def get_progress(self):
        if len(self.path) <= 1:
            return 0.0
        return 100.0 * float(self.visited.mean())

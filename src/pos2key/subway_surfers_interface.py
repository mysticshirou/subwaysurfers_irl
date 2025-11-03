from flask_socketio import SocketIO, emit
from enum import Enum

class KeyboardEventError(Exception):
    # Makes error appear in main namespace (KeyboardEventError: <exception> vs classes.KeyboardEventError: <exception>)
    __module__ = "__main__"

    def __init__(self, error_message: str) -> None:
        # Prints error message received
        super().__init__(error_message)

class KeyboardEventManager():
    def __init__(self, socketio) -> None:
        """
        Initialise SocketIO connection
        """
        self.socketio = socketio
        self.is_paused = False

    def _jump(self) -> str:
        self.socketio.emit('triggerKeyboard', {'key': 'ArrowUp', "code": 38})
        return "Jump"

    def _roll(self) -> str:
        self.socketio.emit('triggerKeyboard', {'key': 'ArrowDown', "code": 40})
        return "Roll"

    def _left(self) -> str:
        self.socketio.emit('triggerKeyboard', {'key': 'ArrowLeft', "code": 37})
        return "Left"

    def _right(self) -> str:
        self.socketio.emit('triggerKeyboard', {'key': 'ArrowRight', "code": 39})
        return "Right"

    def toggle_pause(self) -> str:
        self.socketio.emit('triggerKeyboard', {'key': 'Escape', "code": 27})
        self.is_paused = not self.is_paused
        self.socketio.emit('syncStatus', {'syncState': self.is_paused})
        return "Pause"
    
    def start_game(self) -> str:
        self.socketio.emit('triggerKeyboard', {'key': 'Enter', "code": 13})
        return "Start"

class Grid(Enum):
    """
              Left   Centre   Right
    Jump    (-1,  1) (0,  1) (1,  1)
    Neutral (-1,  0) (0,  0) (1,  0)
    Roll    (-1, -1) (0, -1) (1, -1)

          X  Y
        (-1, 1)
    """

    LEFT_JUMP = {"x": -1, "y": 1}
    CENTRE_JUMP = {"x": 0, "y": 1}
    RIGHT_JUMP = {"x": 1, "y": 1}
    LEFT_NEUTRAL = {"x": -1, "y": 0}
    CENTRE_NEUTRAL = {"x": 0, "y": 0}
    RIGHT_NEUTRAL = {"x": 1, "y": 0}
    LEFT_ROLL = {"x": -1, "y": -1}
    CENTRE_ROLL = {"x": 0, "y": -1}
    RIGHT_ROLL = {"x": 1, "y": -1}

class SubwaySurfer(KeyboardEventManager):
    def __init__(self, socketio, position: dict[str, int] = Grid.CENTRE_NEUTRAL.value) -> None:
        super().__init__(socketio)

        # Initialise default character position (In the centre column, neutral position = CENTRE_NEUTRAL)
        self.x = position["x"]
        self.y = position["y"]

    def _moveX(self, x_distance: int) -> str:
        """
        Determines the X direction by checking whether x_distance is positive or negative. 
        """
        print("right"  if x_distance >= 0 else "left")
        return self._right() if x_distance >= 0 else self._left()
    
    def _moveY(self, y_distance: int) -> str:
        """
        Determines the Y direction by checking whether x_distance is positive or negative. 
        """
        print("jump"  if y_distance >= 0 else "roll")
        return self._jump() if y_distance >= 0 else self._roll()

    def move_to(self, desired_position: Grid) -> None:
        """
                  Left   Centre   Right
        Jump    (-1,  1) (0,  1) (1,  1)
        Neutral (-1,  0) (0,  0) (1,  0)
        Roll    (-1, -1) (0, -1) (1, -1)

              X  Y
            (-1, 1)
        """
        print(f"Moving to {desired_position}")

        # Calculates X & Y distances to travel by finding the difference between the desired and current positions.
        x_distance_to_travel = desired_position["x"] - self.x
        y_distance_to_travel = desired_position["y"] - self.y
        print(f"Current Pos: {self.x, self.y}, Desired Pos: {desired_position}. X Distance: {x_distance_to_travel}, Y Distance: {y_distance_to_travel}")

        # Executes movements
        for _ in range(abs(x_distance_to_travel)):
            print(self._moveX(x_distance_to_travel))

        for _ in range(abs(y_distance_to_travel)):
            self._moveY(y_distance_to_travel)

        # Sets desired X position to be the new current positon.
        # Y positon does not need to be set as it auto resolves itself (Character will stop jumping / rolling automatically). 
        self.x = desired_position["x"]

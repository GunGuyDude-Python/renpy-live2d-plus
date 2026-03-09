from __future__ import annotations
from pathlib import Path
import json
import queue
import random

FPS = 30.0
default_fade_time = 1.0
default_transition_time = 1.0

#######################################################################################################################

# Class for Motion segments.
# For type, 0 = linear, 1 = bezier, 2 = stepped, 3 = inverse stepped
# For each vertex, v[0] is time, v[1] is value
# v1 & v2 are only used for bezier type
class Segment:
    def __init__(self, type: int, 
                 v0: tuple[float, float], 
                 v3: tuple[float, float], 
                 v1: tuple[float, float] = (0.0, 0.0),
                 v2: tuple[float, float] = (0.0, 0.0)
                 ) -> None:
        self.type: int = type
        self.v0: tuple[float, float] = v0
        self.v1: tuple[float, float] = v1
        self.v2: tuple[float, float] = v2
        self.v3: tuple[float, float] = v3
        return

    def __str__(self) -> str:
        output: str = f'Type: {self.type}\n'
        output += f'Starting vertex: t={self.v0[0]}, val={self.v0[1]}\n'
        output += f'Stopping vertex: t={self.v3[0]}, val={self.v3[1]}'
        if self.type is 1:
            output += f'\nBezier vertex 1: t={self.v1[0]}, val={self.v1[1]}\n'
            output += f'Bezier vertex 2: t={self.v2[0]}, val={self.v2[1]}'
        return output
    
    # Read raw list and return instantiated segment objects in a list
    @staticmethod
    def load(input: list[float]) -> list[Segment]:
        casted = [float(x) for x in input]
        output: list[Segment] = list()
        ptr: int = 0
        while (ptr+2 < len(input)):
            type: int = int(casted[ptr+2])
            v0: tuple[float, float] = (casted[ptr], casted[ptr+1])
            # Bezier type
            if type is 1:
                v1: tuple[float, float] = (casted[ptr+3], casted[ptr+4])
                v2: tuple[float, float] = (casted[ptr+5], casted[ptr+6])
                v3: tuple[float, float] = (casted[ptr+7], casted[ptr+8])
                output.append(Segment(type, v0, v1=v1, v2=v2, v3=v3))
                ptr += 7
            # Linear or stepped type
            else:
                v3: tuple[float, float] = (casted[ptr+3], casted[ptr+4])
                output.append(Segment(type, v0, v3))
                ptr += 3
        return output

# Class for Motion curves.
class Curve:
    def __init__(self, target: str, id: str, segments: list[Segment]) -> None:
        self.target: str = target
        self.id: str = id
        self.segments: list[Segment] = segments
        return

    def __str__(self) -> str:
        output: str = f'Target: {self.target}\nID: {self.id}\n'
        for segment in self.segments:
            output += f'\n'
            output += segment.__str__()
        return output
    
    # Read raw list and return instantiated curve objects in a list
    @staticmethod
    def load(input: list[dict]) -> list[Curve]:
        output: list[Curve] = list()
        for curve in input:
            target: str = str(curve['Target'])
            id: str = str(curve['Id'])
            segments: list[Segment] = Segment.load(curve['Segments'])
            output.append(Curve(target, id, segments))
        return output

class Motion:
    pass

class Param:
    pass

class Expression:
    pass

class Model:
    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError('Model name must be a string')
        self.name: str = name
        return
    
    def __str__(self):
        out: str = str()
        return out
    
#######################################################################################################################
#                                                                                                                     #
#                                                   USER FUNCTIONS                                                    #
#                                                                                                                     #
#######################################################################################################################
    


#######################################################################################################################

# Static function
# Load a Live2D model given its directory path
def load_model(game_dir: str, file_name: str) -> Model:
    live2d_path = Path(game_dir) / 'live2d' / file_name
    # Check if directory is a Live2D model folder
    if live2d_path.is_dir() and (live2d_path / (file_name + '.model3.json')).is_file():
        # Create an empty model
        model = Model(file_name)
        motions_dir = live2d_path / 'Motions'
        expressions_dir = live2d_path / 'Expressions'

        # Read each motion and populate the model
        for motion_entry in motions_dir.iterdir():
            motion_path = motions_dir / motion_entry
            if motion_path.is_file():
                motion = load_motion(motion_path)
                model.motions[motion.name.split('.')[0]] = motion

        # Read each expression and populate the model
        for expression_entry in expressions_dir.iterdir():
            expression_path = expressions_dir / expression_entry
            if expression_path.is_file():
                expression = load_expression(expression_path)
                model.expressions[expression.name.split('.')[0]] = expression
    
    # Folder not found or Live2D files not found
    else:
        raise OSError(f'{live2d_path} is not a valid path')
    return model

# Static function
# Load a Live2D motion given its directory path
def load_motion(file_path: Path) -> Motion:
    with open(file_path, 'r') as file:
        data = json.load(file, parse_int=float)
        motion = Motion(file_path.name.split('.')[0], data['Meta']['Duration'], data['Curves'])
    return motion

# Static function
# Load a Live2D expression given its directory path
def load_expression(file_path: Path) -> Expression:
    with open(file_path, 'r') as file:
        data = json.load(file, parse_int=float)
        expression = Expression(file_path.name.split('.')[0], data['Parameters'])
    return expression

# Static function
# Set the default fade duration
def set_fade_default_time(duration: float) -> None:
    global default_fade_time
    if not (isinstance(duration, float) or isinstance(duration, int)):
        raise TypeError('Duration must be a float')
    default_fade_time = float(duration)
    return

# Static function
# Set the default transition duration
def set_transition_default_time(duration: float) -> None:
    global default_transition_time
    if not (isinstance(duration, float) or isinstance(duration, int)):
        raise TypeError('Duration must be a float')
    default_transition_time = float(duration)
    return

# Static function
# Solve for y given st (x) in a linear equation
def linear(st: float, p0: tuple[float, float], p1: tuple[float, float]) -> float:
    # Normalise st to t
    t = (st-p0[0]) / (p1[0]-p0[0])
    y = t*(p1[1]-p0[1]) + p0[1]
    return y

# Static function
# Solve for y given st (x) in a cubic bezier
def bezier(st: float, p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> float:
    # Normalise st to t
    t = (st-p0[0]) / (p3[0]-p0[0])
    y = (1-t)**3 * p0[1] + 3*t*(1-t)**2 * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
    return y
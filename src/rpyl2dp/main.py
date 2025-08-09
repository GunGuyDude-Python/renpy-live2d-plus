import os
from os import path
import json

global my_path
my_path = "D:\\Tools\\Ren'Py\\projects\\Testing\\game\\live2d\\G2MimiruSprite"

class Model:
    def __init__(self, name: str):
        self.name = name
        self.motions = dict()
        return
    
    def __str__(self):
        out = str()
        out += f'Model name: {self.name} - '
        for motion in self.motions:
            out += f'Motion name: {motion} '
        return out
    
    def play(self, motion_name: str) -> None:
        if not isinstance(motion_name, str):
            raise TypeError('Motion name must be a string')
        elif motion_name not in self.motions:
            raise KeyError('No motion with the given name is associated with this model')
        else:
            if isinstance(self.motions[motion_name], Motion):
                print(self.motions[motion_name].curves)
            elif isinstance(self.motions[motion_name], Expression):
                print(self.motions[motion_name].parameters)
            else:
                raise TypeError('Motion has an unknown class')
        return

class Motion:
    def __init__(self, name: str, duration: str, loop: bool, curves: list):
        if not isinstance(name, str):
            raise TypeError('Name must be a string')
        elif not isinstance(duration, float):
            raise TypeError('Duration must be an float')
        elif not isinstance(loop, bool):
            raise TypeError('Loop must be a bool')
        elif not isinstance(curves, list):
            raise TypeError('Curves must be a list')
        else:
            self.name = name
            self.duration = duration
            self.loop = loop
            self.curves = curves
            return
    
    def __str__(self):
        return f'Name: {self.name} - Duration: {self.duration} - Loop: {self.loop} - Curves: {self.curves}'

class Expression:
    def __init__(self, name: str, parameters: list):
        if not isinstance(name, str):
            raise TypeError('Name must be a string')
        elif not isinstance(parameters, list):
            raise TypeError('Parameters must be a list')
        else:
            self.name = name
            self.parameters = parameters
            return
        
    def __str__(self):
        return f'Name: {self.name} - Parameters: {self.parameters}'
    
# Static function
# Load a Live2D model given its directory path
def load_model(folder_path: str) -> Model:
    # Check if directory is a Live2D model folder
    if path.isdir(folder_path) and path.isfile(path.join(folder_path, path.basename(folder_path) + '.model3.json')):
        # Create an empty model
        model = Model(path.basename(folder_path))
        motions_dir = path.join(folder_path, 'Motions')
        expressions_dir = path.join(folder_path, 'Expressions')

        # Read each motion and populate the model
        for motion_entry in os.listdir(motions_dir):
            motion_path = path.join(motions_dir, motion_entry)
            if path.isfile(motion_path):
                motion = load_motion(motion_path)
                model.motions[motion.name] = motion

        # Read each expression and populate the model
        for expression_entry in os.listdir(expressions_dir):
            expression_path = path.join(expressions_dir, expression_entry)
            if path.isfile(expression_path):
                expression = load_expression(expression_path)
                model.motions[expression.name] = expression
    
    # Folder not found or Live2D files not found
    else:
        raise OSError('Live2D model not found')
    return model

# Static function
# Load a Live2D motion given its directory path
def load_motion(file_path: str) -> Motion:
    with open(file_path, 'r') as file:
        data = json.load(file, parse_int=float)
        motion = Motion(path.basename(file_path).split('.')[0], data['Meta']['Duration'], data['Meta']['Loop'], data['Curves'])
        #print(motion.__str__())
    return motion

# Static function
# Load a Live2D expression given its directory path
def load_expression(file_path: str) -> Expression:
    with open(file_path, 'r') as file:
        data = json.load(file, parse_int=float)
        expression = Expression(path.basename(file_path).split('.')[0], data['Parameters'])
        #print(expression.__str__())
    return expression

# Static function
# Solve for y given st (x) in a linear equation
def linear(st: float, p0: tuple[float], p1: tuple[float]) -> float:
    # Normalise st to t
    t = st-p0[0] / p1[0]-p0[0]
    y = (p0[1]+p1[1]) * t
    return y

# Static function
# Solve for y given st (x) in a cubic bezier
def cubic_bezier(st: float, p0: tuple[float], p1: tuple[float], p2: tuple[float], p3: tuple[float]) -> float:
    # Normalise st to t
    t = st-p0[0] / p3[0]-p0[0]
    y = (1-t)**3 * p0[1] + 3*t*(1-t)**2 * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
    return y
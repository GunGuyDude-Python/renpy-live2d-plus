import os
from os import path
import json
import queue

global my_path
my_path = "D:\\Tools\\Ren'Py\\projects\\Testing\\game\\live2d\\G2MimiruSprite"

class Model:
    def __init__(self, name: str):
        self.name = name
        self.motions = dict()
        self.exclusive = Exclusive()
        self.inclusive = Inclusive()
        return
    
    def __str__(self):
        out = str()
        out += f'Model name: {self.name} - '
        for motion in self.motions:
            out += f'Motion name: {motion} '
        return out
    
    def exclusive_push(self, wait_seconds: float, animation_name: str) -> None:
        self.exclusive.push(wait_seconds, animation_name)
        return
    
    def exclusive_pop(self) -> tuple[float, str]:
        return self.exclusive.pop()
    
    def exclusive_empty(self) -> bool:
        return self.exclusive.exclusive_queue.empty()
    
    def inclusive_add(self, min_seconds: float, max_seconds: float, animation_name: str) -> None:
        self.inclusive.add(min_seconds, max_seconds, animation_name)
        return
    
    def inclusive_remove(self, animation_name: str) -> None:
        self.inclusive.remove(animation_name)
        return

    # WIP
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

    # Find the value of every parameter of this motion at this second
    def second(self, motion_name: str, st: float) -> float:
        values = list()
        if not isinstance(motion_name, str):
            raise TypeError('Motion name must be a string')
        elif not (isinstance(st, float) or isinstance(st, int)):
            raise TypeError('Seconds must be a float')
        elif motion_name not in self.motions:
            raise KeyError('No motion with the given name is associated with this model')
        else:
            if isinstance(self.motions[motion_name], Motion):
                # Find the value of every parameter of this motion at this second
                if st > self.motions[motion_name].duration:
                    raise ValueError('Requested seconds is longer than motion duration')
                else:
                    for curve in self.motions[motion_name].curves:
                        target = curve['Target']
                        id = curve['Id']
                        segments = curve['Segments']
                        row = 2
                        while((segments[row+5] < st) if (segments[row] == 1) else (segments[row+1] < st)):
                            if segments[row] == 0:
                                # Linear segment
                                row += 3
                            elif segments[row] == 1:
                                # Bezier segment
                                row += 7
                            elif segments[row] == 2 or segments[row] == 3:
                                raise ValueError('Stepped and inverse-stepped segments are unsupported')
                            else:
                                raise ValueError('Unknown segment type')
                        p0 = (segments[row-2], segments[row-1])
                        p1 = (segments[row+1], segments[row+2])
                        if segments[row] == 1:
                            p2 = (segments[row+3], segments[row+4])
                            p3 = (segments[row+5], segments[row+6])
                            value = cubic_bezier(st, p0, p1, p2, p3)
                        else:
                            value = linear(st, p0, p1)
                        values.append({'Target': target, 'Id': id, 'Value': value})

            elif isinstance(self.motions[motion_name], Expression):
                # Find the value of every parameter of this expression
                values = self.motions[motion_name].parameters.copy()
            else:
                raise TypeError('Motion has an unknown class')
        return values

# Parent class for motions and animations
class Animation:
    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError('Name must be a string')
        else:
            self.name = name
            return

    def __str__(self):
        return f'Name: {self.name}'

# Class for motions
class Motion(Animation):
    def __init__(self, name: str, duration: float, loop: bool, curves: list):
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

# Class for expressions
class Expression(Animation):
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
    
# Exclusive animations use a FIFO queue. Exclusive animations can only play one at a time.
class Exclusive:
    def __init__(self):
        self.exclusive_queue = queue.Queue()
        return

    def push(self, wait_seconds: float, animation_name: str) -> None:
        if not isinstance(wait_seconds, float):
            raise TypeError('Wait seconds must be a float')
        elif not isinstance(animation_name, str):
            raise TypeError('Animation name must be a string')
        else:
            self.exclusive_queue.put((wait_seconds, animation_name))
            return
    
    def pop(self) -> tuple[float, str]:
        if self.exclusive_queue.empty():
            return None
        else:
            (wait_seconds, animation_name) = self.exclusive_queue.get()
            return (wait_seconds, animation_name)

# Inclusive animations use a dict. All inclusive animations in the dict can play simultaneously.
class Inclusive:
    def __init__(self):
        self.inclusive_dict = dict()
        return

    def add(self, min_seconds: float, max_seconds: float, animation_name: str) -> None:
        if not isinstance(min_seconds, float):
            raise TypeError('Minimum seconds must be a float')
        elif not isinstance(max_seconds, float):
            raise TypeError('Maximum seconds must be a float')
        elif not isinstance(animation_name, str):
            raise TypeError('Animation name must be a string')
        else:
            self.inclusive_dict[animation_name] = (min_seconds, max_seconds)
            return

    def remove(self, animation_name: str) -> None:
        if not isinstance(animation_name, str):
            raise TypeError('Animation name must be a string')
        elif animation_name not in self.inclusive_dict:
            return
        else:
            self.inclusive_dict.pop(animation_name)
            return

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
def linear(st: float, p0: tuple[float, float], p1: tuple[float, float]) -> float:
    # Normalise st to t
    t = (st-p0[0]) / (p1[0]-p0[0])
    y = t*(p1[1]-p0[1]) + p0[1]
    return y

# Static function
# Solve for y given st (x) in a cubic bezier
def cubic_bezier(st: float, p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> float:
    # Normalise st to t
    t = (st-p0[0]) / (p3[0]-p0[0])
    y = (1-t)**3 * p0[1] + 3*t*(1-t)**2 * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
    return y
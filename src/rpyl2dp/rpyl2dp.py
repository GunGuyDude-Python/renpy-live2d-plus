import os
from os import path
import json
import queue
import random

global FPS
FPS = 30.0
global DEFAULT_FADE_TIME
DEFAULT_FADE_TIME = 1.0
global DEFAULT_TRANSITION_TIME
DEFAULT_TRANSITION_TIME = 1.0

#######################################################################################################################

# Class for motions
class Motion():
    def __init__(self, name: str, duration: float, curves: list):
        if not isinstance(name, str):
            raise TypeError('Name must be a string')
        elif not (isinstance(duration, float) or isinstance(duration, int)):
            raise TypeError('Duration must be an float')
        elif not isinstance(curves, list):
            raise TypeError('Curves must be a list')
        else:
            self.name: str = name
            self.duration: float = float(duration)
            self.curves: list = curves
            return
    
    def __str__(self):
        return f'Name: {self.name}\nDuration: {self.duration}\nCurves: {self.curves}'

# Class for expressions
class Expression():
    def __init__(self, name: str, parameters: list):
        if not isinstance(name, str):
            raise TypeError('Name must be a string')
        elif not isinstance(parameters, list):
            raise TypeError('Parameters must be a list')
        else:
            self.name: str = name
            self.parameters: list = parameters
            return
        
    def __str__(self):
        return f'Name: {self.name}\nParameters: {self.parameters}'
    
# Exclusive animations use a FIFO queue. Exclusive animations can only play one at a time.
class Exclusive:
    def __init__(self):
        self.exclusive_queue: queue.Queue = queue.Queue()
        return

    def push(self, motion_name: str, wait_seconds: float, loop: bool) -> None:
        if not isinstance(motion_name, str):
            raise TypeError('Motion name must be a string')
        elif not (isinstance(wait_seconds, float) or isinstance(wait_seconds, int)):
            raise TypeError('Wait seconds must be a float')
        elif not isinstance(loop, bool):
            raise TypeError('Loop must be a bool')
        else:
            self.exclusive_queue.put((motion_name, float(wait_seconds), loop))
            return
    
    def pop(self) -> tuple[str, float, bool]:
        if self.exclusive_queue.empty():
            return None
        else:
            (motion_name, wait_seconds, loop) = self.exclusive_queue.get()
            return (motion_name, wait_seconds, loop)

# Inclusive animations use a dict. All inclusive animations in the dict can play simultaneously.
class Inclusive:
    def __init__(self):
        self.inclusive_dict: dict = dict()
        return

    def add(self, motion_name: str, min_seconds: float, max_seconds: float) -> None:
        if not isinstance(motion_name, str):
            raise TypeError('Motion name must be a string')
        elif not (isinstance(min_seconds, float) or isinstance(min_seconds, int)):
            raise TypeError('Minimum seconds must be a float')
        elif not (isinstance(max_seconds, float) or isinstance(max_seconds, int)):
            raise TypeError('Maximum seconds must be a float')
        else:
            self.inclusive_dict[motion_name] = (float(min_seconds), float(max_seconds), 0.0, 0.0)
            return

    def remove(self, motion_name: str) -> None:
        if not isinstance(motion_name, str):
            raise TypeError('Motion name must be a string')
        elif motion_name not in self.inclusive_dict:
            return
        else:
            self.inclusive_dict.pop(motion_name)
            return

# Active expressions use a dict. All active expressions are shown simultaneously.
class ActiveExpressions:
    def __init__(self):
        self.expressions_dict: dict = dict()
        return
    
    def add(self, expression_name: str, fade_in_time: float, fade_out_time: float) -> None:
        if not isinstance(expression_name, str):
            raise TypeError('Expression name must be a string')
        elif not (isinstance(fade_in_time, float) or isinstance(fade_in_time, int)):
            raise TypeError('Fade in time must be a float')
        elif not (isinstance(fade_out_time, float) or isinstance(fade_out_time, int)):
            raise TypeError('Fade out time must be a float')
        else:
            self.expressions_dict[expression_name] = (float(fade_in_time), float(fade_out_time))
            return

    def remove(self, expression_name: str) -> None:
        if not isinstance(expression_name, str):
            raise TypeError('Expression name must be a string')
        elif expression_name not in self.expressions_dict:
            return
        else:
            self.expressions_dict.pop(expression_name)
            return

#######################################################################################################################

class Model:
    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError('Model name must be a string')
        self.name: str = name
        self.motions: dict = dict()
        self.expressions: dict = dict()
        self.exclusive: Exclusive = Exclusive()
        self.inclusive: Inclusive = Inclusive()
        self.active_expressions: ActiveExpressions = ActiveExpressions()
        self.action: Motion = None
        self.action_start_time: float = 0.0
        self.action_end_time: float = 0.0
        self.action_loop: bool = False
        self.persistent: dict = dict()
        self.st: float = 0.0
        self.sequential_name = 0
        return
    
    def __str__(self):
        out: str = str()
        out += f'Model name: {self.name}\n'
        for motion in self.motions:
            out += f'Motion name: {motion}\n'
        for expression in self.expressions:
            out += f'Expression name: {expression}\n'
        return out
    
#######################################################################################################################
#                                                                                                                     #
#                                                   USER FUNCTIONS                                                    #
#                                                                                                                     #
#######################################################################################################################
    
    # Returns a dict of motions currently playing or queued
    def list_active(self) -> dict[list[str]]:
        values: dict = dict()
        exclusives: list = list()
        inclusives: list = list()
        expressions: list = list()
        if self.action is not None:
            exclusives.append(self.action.name)
        for (motion_name, wait_seconds, loop) in list(self.exclusive.exclusive_queue.queue):
            exclusives.append(motion_name)
        for (k, v) in self.inclusive.inclusive_dict.items():
            inclusives.append(k)
        for (k, v) in self.active_expressions.expressions_dict.items():
            expressions.append(k)
        values['Exclusive motions'] = exclusives
        values['Inclusive motions'] = inclusives
        values['Expressions'] = expressions
        return values

    # Push a motion to the exclusive queue
    def exclusive_push(self, motion_name: str, wait_seconds: float=0, loop: bool=True) -> None:
        self.exclusive.push(motion_name, wait_seconds, loop)
        return
    
    # Pop a motion from the exclusive queue
    def exclusive_pop(self) -> tuple[str, float, bool]:
        return self.exclusive.pop()
    
    # Returns True if exclusive queue is empty
    def exclusive_empty(self) -> bool:
        return self.exclusive.exclusive_queue.empty()

    # Skip playing the current motion
    def exclusive_skip(self) -> None:
        if self.exclusive_empty():
            self.action = None
            self.action_loop = False
            self.action_start_time = 0.0
            self.action_end_time = 0.0
            return
        else:
            (motion_name, wait_seconds, loop) = self.exclusive_pop()
            self.action = self.motions[motion_name]
            self.action_loop = loop
            self.action_start_time = self.st + wait_seconds
            self.action_end_time = self.action_start_time + self.action.duration
            return
        
    # Skip all motions in the queue
    def exclusive_skipall(self) -> None:
        while(not self.exclusive_empty()):
            self.exclusive_skip()
        self.exclusive_skip()
    
    # Add a motion to the inclusive set
    def inclusive_add(self, motion_name: str, min_seconds: float=0, max_seconds: float=0) -> None:
        self.inclusive.add(motion_name, min_seconds, max_seconds)
        return
    
    # Remove a motion from the inclusive set
    def inclusive_remove(self, motion_name: str) -> None:
        self.inclusive.remove(motion_name)
        return
    
    # Remove all motions from the inclusive set
    def inclusive_removeall(self) -> None:
        self.inclusive.inclusive_dict.clear()
    
    # Activate an expression
    def expression_add(self, expression_name: str, fade_in_time: float=DEFAULT_FADE_TIME, fade_out_time: float=DEFAULT_FADE_TIME) -> None:
        self.active_expressions.add(expression_name, fade_in_time, fade_out_time)
        return
    
    # Deactivate an expression
    def expression_remove(self, expression_name: str) -> None:
        self.active_expressions.remove(expression_name)
        return
    
    # Deactivate all expressions
    def expression_removeall(self) -> None:
        self.active_expressions.expressions_dict.clear()
    
    # Reset the model and its variables
    def reset(self) -> None:
        self.exclusive_skipall()
        self.inclusive_removeall()
        self.expression_removeall()
        self.persistent.clear()

    # Call every frame to animate
    def update(self, renpy_model, st: float) -> float:
        self.st = st
        self.force_persistence(renpy_model)
        self.animate_exclusive(renpy_model)
        self.animate_inclusive(renpy_model)
        self.animate_expression(renpy_model)
        return 1.0/FPS
    
#######################################################################################################################

    # Make it so when exclusive motions end they do not revert parameters to default values
    def force_persistence(self, renpy_model) -> None:
        for (target, id), value in self.persistent.items():
            if target == 'Model' and id == 'Opacity':
                # WIP
                pass
            # Part parameter value
            elif target == 'Parameter':
                renpy_model.blend_parameter(id, "Overwrite", value)
            # Part opacity
            elif target == 'PartOpacity':
                renpy_model.blend_opacity(id, "Overwrite", value)

    # Call every frame to animate exclusive motions
    def animate_exclusive(self, renpy_model) -> None:
        # If currently idle, check queue
        if self.st >= self.action_end_time:
            # If queue empty and looping, add motion to the queue again
            if self.exclusive_empty() and self.action_loop == True:
                self.exclusive_push(self.action.name, 0, self.action_loop)
                self.exclusive_skip()
            # If queue empty and not looping, do nothing
            elif self.exclusive_empty():
                pass
            # Otherwise pop from queue and play motion
            else:
                self.exclusive_skip()
            return
        
        # If currently playing a motion, set model parameters
        elif self.st >= self.action_start_time:
            relative_st = self.st - self.action_start_time
            # Failsafe for if the motion has finished playing but program thinks it's still playing
            if relative_st > self.action.duration:
                pass
            else:
                params = self.second(self.action.name, relative_st)
                for param in params:
                    # Model opacity
                    if param['Target'] == 'Model' and param['Id'] == 'Opacity':
                        # WIP
                        pass
                    # Part parameter value
                    elif param['Target'] == 'Parameter':
                        renpy_model.blend_parameter(param['Id'], "Overwrite", param['Value'])
                    # Part opacity
                    elif param['Target'] == 'PartOpacity':
                        renpy_model.blend_opacity(param['Id'], "Overwrite", param['Value'])
                    self.persistent[(param['Target'], param['Id'])] = param['Value']
            return
        
        # Else motion is waiting to start
        else:
            return
        
    # Call every frame to animate inclusive animations
    def animate_inclusive(self, renpy_model) -> None:
        for motion_name, (min_seconds, max_seconds, start_time, end_time) in self.inclusive.inclusive_dict.items():
            # If motion has finished playing, randomise a new wait time before looping
            if motion_name not in self.motions:
                raise KeyError(f'No motion with the name {motion_name} associated with model {self.name}')
            elif self.st > end_time:
                rand = min_seconds + (max_seconds - min_seconds) * random.random()
                self.inclusive.inclusive_dict[motion_name] = (min_seconds, max_seconds, self.st + rand, self.st + self.motions[motion_name].duration + rand)

        # Refresh values after updating
        for motion_name, (min_seconds, max_seconds, start_time, end_time) in self.inclusive.inclusive_dict.items():
            relative_st = self.st - start_time
            if relative_st > end_time - start_time:
                # Failsafe for impossible end time value
                relative_st = end_time - start_time
            
            # If motion is currently playing
            if relative_st > 0:
                params = self.second(motion_name, relative_st)
                for param in params:
                    # Model opacity
                    if param['Target'] == 'Model' and param['Id'] == 'Opacity':
                        # WIP
                        pass
                    # Part parameter value
                    elif param['Target'] == 'Parameter':
                        renpy_model.blend_parameter(param['Id'], "Overwrite", param['Value'])
                    # Part opacity
                    elif param['Target'] == 'PartOpacity':
                        renpy_model.blend_opacity(param['Id'], "Overwrite", param['Value'])

            # Else motion is waiting to start
            else:
                pass
        return
    
    # Call every frame to set expressions
    def animate_expression(self, renpy_model) -> None:
        for expression_name, (fade_in_time, fade_out_time) in self.active_expressions.expressions_dict.items():
            for param in self.expressions[expression_name].parameters:
                renpy_model.blend_parameter(param['Id'], "Overwrite", param['Value'])
        return

    # Find the value of every parameter of this motion at this second
    def second(self, motion_name: str, relative_st: float) -> list[dict]:
        values: list = list()
        if not isinstance(motion_name, str):
            raise TypeError('Motion name must be a string')
        elif not (isinstance(relative_st, float) or isinstance(relative_st, int)):
            raise TypeError('Seconds must be a float')
        elif motion_name not in self.motions:
            raise KeyError(f'No motion with the name "{motion_name}" associated with model "{self.name}"')
        else:
            # Find the value of every parameter of this motion at this second
            if relative_st > self.motions[motion_name].duration:
                # Failsafe for if relative st is greater than entire length of motion
                relative_st = self.motions[motion_name].duration
                
            for curve in self.motions[motion_name].curves:
                target = curve['Target']
                id = curve['Id']
                segments = curve['Segments']
                row = 2
                
                loop = True
                while(loop):
                    if segments[row] == 0:
                        # Linear segment
                        if relative_st < segments[row+1] or len(segments) <= row+3:
                            loop = False
                        else:
                            row += 3
                    elif segments[row] == 1:
                        # Bezier segment
                        if relative_st < segments[row+5] or len(segments) <= row+7:
                            loop = False
                        else:
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
                    value = bezier(relative_st, p0, p1, p2, p3)
                else:
                    value = linear(relative_st, p0, p1)
                values.append({'Target': target, 'Id': id, 'Value': value})
        return values

#######################################################################################################################

    # Transition from the current pose to the beginning of the provided one
    def transition_to(self, motion_name: str, type: str='bezier', duration: float=DEFAULT_TRANSITION_TIME) -> str:
        if not isinstance(motion_name, str):
            raise TypeError('Motion name must be a string')
        elif motion_name not in self.motions:
            raise KeyError(f'No motion with the name "{motion_name}" associated with model "{self.name}"')
        if not isinstance(type, str):
            raise TypeError('Type must be "linear" or "bezier"')
        elif not (type == 'linear' or type == 'bezier'):
            raise ValueError(f'"{type}" is not a valid type. Choose "linear" or "bezier"')
        elif not (isinstance(duration, float) or isinstance(duration, int)):
            raise TypeError('Duration must be a float')
        
        transitions = dict()
        for curve in self.motions[motion_name].curves:
            target = curve['Target']
            id = curve['Id']
            segments = curve['Segments']
            transitions[(target, id)] = segments[1]

        if len(self.persistent) <= 0:
            transitions.clear()
            transitions[('Model', 'Opacity')] = [0, 1, 0, duration, 1]
        else:
            for (target, id) in transitions:
                if (target, id) in self.persistent:
                    p31 = transitions[(target, id)]
                    p01 = self.persistent[(target, id)]
                    if type == 'linear':
                        transitions[(target, id)] = [0, p01, 0, duration, p31]
                    elif type == 'bezier':
                        transitions[(target, id)] = [0, p01, 1, duration/3, p01, duration*2/3, p31, duration, p31]
                    else:
                        raise ValueError()
                
        curves = list()
        for (target, id) in transitions:
            if isinstance(transitions[(target, id)], list):
                curves.append({'Target': target, 'Id': id, 'Segments': transitions[(target, id)]})
        new_motion_name = 'transition' + str(self.sequential_name)
        self.sequential_name += 1
        new_motion = Motion(new_motion_name, duration, curves)
        self.motions[new_motion_name] = new_motion
        
        return new_motion_name

#######################################################################################################################

# Static function
# Load a Live2D model given its directory path
def load_model(folder_path: str) -> Model:
    # Check if directory is a Live2D model folder
    if path.isdir(folder_path) and path.isfile(path.join(folder_path, path.basename(folder_path) + '.model3.json')):
        # Create an empty model
        model = Model(path.basename(folder_path).split('.')[0])
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
                model.expressions[expression.name] = expression
    
    # Folder not found or Live2D files not found
    else:
        raise OSError('Live2D model not found')
    return model

# Static function
# Load a Live2D motion given its directory path
def load_motion(file_path: str) -> Motion:
    with open(file_path, 'r') as file:
        data = json.load(file, parse_int=float)
        motion = Motion(path.basename(file_path).split('.')[0], data['Meta']['Duration'], data['Curves'])
    return motion

# Static function
# Load a Live2D expression given its directory path
def load_expression(file_path: str) -> Expression:
    with open(file_path, 'r') as file:
        data = json.load(file, parse_int=float)
        expression = Expression(path.basename(file_path).split('.')[0], data['Parameters'])
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
def bezier(st: float, p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> float:
    # Normalise st to t
    t = (st-p0[0]) / (p3[0]-p0[0])
    y = (1-t)**3 * p0[1] + 3*t*(1-t)**2 * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
    return y
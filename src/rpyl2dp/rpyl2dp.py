from __future__ import annotations
from pathlib import Path
import json
from queue import Queue
from typing import Any
import random

FPS = 30.0
default_fade_time = 1.0
default_transition_time = 1.0

#######################################################################################################################

# Class for motion segments.
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
        if self.type == 1:
            output += f'Bezier vertex 1: t={self.v1[0]}, val={self.v1[1]}\n'
            output += f'Bezier vertex 2: t={self.v2[0]}, val={self.v2[1]}\n'
        output += f'Stopping vertex: t={self.v3[0]}, val={self.v3[1]}\n'
        return output
    
    # Check if time is within bounds
    def contains(self, st: float) -> bool:
        return (self.v0[0] <= st < self.v3[0])

    # Convert time to parameter value
    def solve(self, st: float) -> float:
        # Raise exception if time is not within bounds
        if (st < self.v0[0]) or (self.v3[0] < st):
            raise ValueError(f'{st} is beyond segment bounds of ({self.v0[0]}, {self.v3[0]})')
        # Linear
        if self.type == 0:
            return self.linear(st, self.v0, self.v3)
        # Bezier
        elif self.type == 1:
            return self.bezier(st, self.v0, self.v1, self.v2, self.v3)
        # Stepped
        elif self.type == 2:
            return self.stepped(st, self.v0, self.v3)
        # Inverse stepped
        elif self.type == 3:
            return self.inv_stepped(st, self.v0, self.v3)
        # Exception
        else:
            raise ValueError(f'{self.type} is not a valid value for segment type.')
    
    # Read raw list and return instantiated segment objects in a list
    @staticmethod
    def load(input: list[float]) -> list[Segment]:
        segments: list[Segment] = list()
        ptr: int = 0
        while (ptr+2 < len(input)):
            # Uncast the type variable, very cursed
            type: int = int(input[ptr+2])
            v0: tuple[float, float] = (input[ptr], input[ptr+1])
            # Bezier type
            if type == 1:
                v1: tuple[float, float] = (input[ptr+3], input[ptr+4])
                v2: tuple[float, float] = (input[ptr+5], input[ptr+6])
                v3: tuple[float, float] = (input[ptr+7], input[ptr+8])
                segments.append(Segment(type, v0, v1=v1, v2=v2, v3=v3))
                ptr += 7
            # Linear or stepped type
            else:
                v3: tuple[float, float] = (input[ptr+3], input[ptr+4])
                segments.append(Segment(type, v0, v3))
                ptr += 3
        return segments
    
    # Solve for y given st (x) in a linear equation
    @staticmethod
    def linear(st: float, p0: tuple[float, float], p1: tuple[float, float]) -> float:
        # Normalise st to t
        t = (st-p0[0]) / (p1[0]-p0[0])
        y = t*(p1[1]-p0[1]) + p0[1]
        return y

    # Solve for y given st (x) in a cubic bezier
    @staticmethod
    def bezier(st: float, p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> float:
        # Normalise st to t
        t = (st-p0[0]) / (p3[0]-p0[0])
        y = (1-t)**3 * p0[1] + 3*t*(1-t)**2 * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
        return y

    # Solve for y given st (x) in a stepped function
    @staticmethod
    def stepped(st: float, p0: tuple[float, float], p1: tuple[float, float]) -> float:
        # Stepped always returns value at first vertex
        y = p0[1]
        return y

    # Solve for y given st (x) in a inverse stepped function
    @staticmethod
    def inv_stepped(st: float, p0: tuple[float, float], p1: tuple[float, float]) -> float:
        # Inverse stepped always returns value at second vertex
        y = p1[1]
        return y

# Class for motion curves.
class Curve:
    def __init__(self, target: str, id: str, segments: list[Segment]) -> None:
        self.target: str = target
        self.id: str = id
        self.segments: list[Segment] = segments
        return

    def __str__(self) -> str:
        output: str = f'\nTarget: {self.target}\nID: {self.id}\n'
        for segment in self.segments:
            output += segment.__str__()
        return output
    
    def solve(self, st: float) -> float:
        if st < 0:
            raise ValueError(f'Time of {st} cannot be smaller than 0')
        for segment in self.segments:
            if segment.contains(st):
                return segment.solve(st)
        # Pad remaining runtime with last valid value
        return self.segments[-1].v3[1]

    # Read raw list and return instantiated curve objects in a dict
    @staticmethod
    def load(input: list[dict]) -> dict[tuple[str, str], Curve]:
        curves: dict[tuple[str, str], Curve] = dict()
        for curve in input:
            target: str = str(curve['Target'])
            id: str = str(curve['Id'])
            segments: list[Segment] = Segment.load(curve['Segments'])
            curves[(target, id)] = Curve(target, id, segments)
        return curves

# Class for model motions
class Motion:
    def __init__(self, name: str, duration: float, curves: dict[tuple[str, str], Curve]) -> None:
        self.name: str = name
        self.duration: float = duration
        self.curves: dict[tuple[str, str], Curve] = curves
        return
    
    def __str__(self) -> str:
        output: str = f'\n\n\nMotion name: {self.name}\nDuration: {self.duration}\n'
        for curve in self.curves.values():
            output += curve.__str__()
        return output

    def solve(self, st: float) -> dict[tuple[str, str], float]:
        if st < 0:
            raise ValueError(f'Time of {st} cannot be smaller than 0')
        if st > self.duration:
            raise ValueError(f'Time of {st} cannot be longer than motion duration')
        values: dict[tuple[str, str], float] = dict()
        for key, curve in self.curves.items():
            value: float = curve.solve(st)
            values[key] = value
        return values

    # Read from file and return instantiated motion object
    @staticmethod
    def load(file_path: Path) -> Motion:
        with open(file_path, 'r') as file:
            data = json.load(file, parse_int=float)
            curves = Curve.load(data['Curves'])
            motion = Motion(file_path.name.split('.')[0], data['Meta']['Duration'], curves)
        return motion

class Param:
    def __init__(self, id: str, value: float, blend: str='') -> None:
        self.id: str = id
        self.value: float = value
        self.blend: str = 'Add'
        if blend in ['Add', 'Overwrite']:
            self.blend = blend
        return
    
    def __str__(self) -> str:
        output: str = f'ID: {self.id}\nValue: {self.value}\nBlend: {self.blend}\n'
        return output
    
    # Read raw list and return instantiated param objects in a dict
    @staticmethod
    def load(input: list[dict]) -> dict[str, Param]:
        params: dict[str, Param] = dict()
        for param in input:
            id: str = str(param['Id'])
            value: float = float(param['Value'])
            blend: str = str(param['Blend'])
            params[id] = Param(id, value, blend)
        return params

class Expression:
    def __init__(self, name: str, params: dict[str, Param]) -> None:
        self.name: str = name
        self.params: dict[str, Param] = params
        return
    
    def __str__(self) -> str:
        output: str = f'\n\n\nExpression name: {self.name}\n'
        for param in self.params.values():
            output += param.__str__()
        return output
    
    # Read from file and return instantiated expression object
    @staticmethod
    def load(file_path: Path) -> Expression:
        with open(file_path, 'r') as file:
            data = json.load(file, parse_int=float)
            params = Param.load(data['Parameters'])
            expression = Expression(file_path.name.split('.')[0], params)
        return expression

# Class for model
class Model:
    def __init__(self, name: str):
        self.name: str = name
        self.motions: dict[str, Motion] = dict()
        self.expressions: dict[str, Expression] = dict()
        return
    
    def __str__(self) -> str:
        output: str = f'Model name: {self.name}'
        for motion in self.motions.values():
            output += motion.__str__()
        return output
    
    @staticmethod
    def load(game_dir: str, file_name: str) -> Model:
        live2d_path = Path(game_dir) / 'live2d' / file_name
        # Check if directory is a Live2D model folder
        if (not live2d_path.is_dir()) or (not (live2d_path / (file_name + '.model3.json')).is_file()):
            raise OSError(f'{live2d_path} is not a valid path')
        # Create an empty model
        model = Model(file_name)
        motions_dir = live2d_path / 'Motions'
        expressions_dir = live2d_path / 'Expressions'
        # Read each motion and populate the model
        for motion_entry in motions_dir.iterdir():
            motion_path = motions_dir / motion_entry
            if motion_path.is_file():
                motion = Motion.load(motion_path)
                model.motions[motion.name.split('.')[0]] = motion
        # Read each expression and populate the model
        for expression_entry in expressions_dir.iterdir():
            expression_path = expressions_dir / expression_entry
            if expression_path.is_file():
                expression = Expression.load(expression_path)
                model.expressions[expression.name.split('.')[0]] = expression
        return model
    
class Exclusive:
    def __init__(self) -> None:
        self.st: float = 0.0
        self.items: Queue[dict[str, Any]] = Queue()
        self.buffer: dict[str, Any] = dict()
        self.start: float = 0.0
        self.end: float = 0.0
        self.crop: float = 0.0
        return
    
    def tick(self, st: float) -> dict[tuple[str, str], float]:
        self.st = st
        # If last motion has ended
        if self.end < self.st:
            # If queue has items
            if not self.is_empty():
                self.skip()
            # If queue is empty and last motion was looping
            elif (not self.buffer) and (self.buffer['loop'] == True):
                temp = self.skip()
                assert(not temp)
                self.items.put(temp)
            # Otherwise player is idle
        # If motion is currently playing
        elif (not self.buffer) and (self.start <= self.st):
            relative_st: float = self.st - self.start + self.crop
            motion: Motion = self.buffer['motion']
            return motion.solve(relative_st)
        # Otherwise player is idle
        return dict()

    def skip(self) -> dict[str, Any]:
        temp = dict()
        if not self.buffer:
            temp = self.buffer.copy()
        if self.is_empty():
            self.buffer = dict()
            self.start = 0.0
            self.end = 0.0
            self.crop = 0.0
        else:
            self.buffer = self.pop()
            # Condition already checked above, use assert to make Pylance happy
            assert(not self.buffer)
            motion: Motion = self.buffer['motion']
            wait_seconds: float = self.buffer['wait_seconds']
            crop_seconds: float = self.buffer['crop_seconds']
            if crop_seconds > motion.duration:
                crop_seconds = motion.duration
            self.start = self.st + wait_seconds
            self.end = self.start + motion.duration - crop_seconds
            self.crop = crop_seconds
        return temp
        
    def clear(self) -> None:
        while not self.is_empty():
            self.skip()
        if not self.buffer:
            self.skip()
        return
    
    def push(self, motion: Motion, wait_seconds: float, crop_seconds: float, loop: bool) -> bool:
        entry: dict[str, Any] = dict()
        entry['motion'] = motion
        entry['wait_seconds'] = wait_seconds
        entry['crop_seconds'] = crop_seconds
        entry['loop'] = loop
        return self.push_raw(entry)
    
    def push_raw(self, entry: dict[str, Any]) -> bool:
        try:
            self.items.put(entry)
        except:
            return False
        return True
    
    def push_many(self, entries: list[dict[str, Any]]) -> list[bool]:
        lst: list[bool] = list()
        for entry in entries:
            lst.append(self.push_raw(entry))
        return lst

    def pop(self) -> dict[str, Any]:
        if self.is_empty():
            return dict()
        return self.items.get()

    def members(self) -> list:
        lst = list(self.items.queue)
        return lst

    def length(self) -> float:
        lst = list(self.items.queue)
        return len(lst)

    def is_empty(self) -> bool:
        return self.items.empty()

class Inclusive:
    def __init__(self) -> None:
        self.st: float = 0.0
        self.items: dict[Motion, tuple[float, float, float, float]]
        return
    
    def tick(self, st: float) -> dict[tuple[str, str], float]:
        self.st = st
        framedata: dict[tuple[str, str], float] = dict()
        # Check each inclusive motion
        for motion, (min_wait, max_wait, start, end) in self.items.items():
            # If current loop has ended
            if end < self.st:
                self.generate_loop(motion)
            # If motion is currently playing
            elif start <= self.st:
                relative_st: float = self.st - start
                framedata.update(motion.solve(relative_st))
        return framedata
    
    def add(self, motion: Motion, min_wait: float, max_wait: float) -> bool:
        entry: tuple[float, float, float, float] = (min_wait, max_wait, 0.0, 0.0)
        return self.add_raw(motion, entry)

    def add_raw(self, motion: Motion, entry: tuple[float, float, float, float]) -> bool:
        try:
            self.items[motion] = entry
        except:
            return False
        return True

    def add_many(self, entries: dict[Motion, tuple[float, float, float, float]]) -> bool:
        try:
            self.items.update(entries)
        except:
            return False
        return True
    
    def remove(self, motion: Motion) -> bool:
        if self.is_empty():
            return False
        try:
            self.items.pop(motion)
        except:
            return False
        return True

    def remove_many(self, motions: list[Motion]) -> list[bool]:
        lst: list[bool] = list()
        for motion in motions:
            lst.append(self.remove(motion))
        return lst

    def generate_loop(self, motion: Motion) -> None:
        duration: float = motion.duration
        (min_wait, max_wait, _, _) = self.items[motion]
        rand = min_wait + (max_wait - min_wait)*random.random()
        start = self.st + rand
        end = start + duration
        self.items[motion] = (min_wait, max_wait, start, end)

    def members(self) -> list:
        lst = list(self.items.items())
        return lst

    def length(self) -> float:
        return len(self.items)

    def is_empty(self) -> bool:
        return not self.items

class ActiveExpr:
    pass
    
#######################################################################################################################
#                                                                                                                     #
#                                                   USER FUNCTIONS                                                    #
#                                                                                                                     #
#######################################################################################################################
    


#######################################################################################################################

# Set the default fade duration
@staticmethod
def set_fade_default_time(duration: float) -> None:
    global default_fade_time
    if not (isinstance(duration, float) or isinstance(duration, int)):
        raise TypeError('Duration must be a float')
    default_fade_time = float(duration)
    return

# Set the default transition duration
@staticmethod
def set_transition_default_time(duration: float) -> None:
    global default_transition_time
    if not (isinstance(duration, float) or isinstance(duration, int)):
        raise TypeError('Duration must be a float')
    default_transition_time = float(duration)
    return

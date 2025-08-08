class ExclusiveMotion:
    def __init__(self, duration, loop, curves):
        if not isinstance(duration, int):
            raise TypeError("Duration must be an integer")
        elif not isinstance(loop, bool):
            raise TypeError("Loop must be a bool")
        elif not isinstance(curves, list):
            raise TypeError("Curves must be a list")
        else:
            self.duration = duration
            self.loop = loop
            self.curves = curves
            return
    
    def __str__(self):
        return f"Duration: {self.duration} - Loop: {self.loop} - Curves: {self.curves}"

class InclusiveMotion:
    def __init__(self, duration, loop, curves):
        if not isinstance(duration, int):
            raise TypeError("Duration must be an integer")
        elif not isinstance(loop, bool):
            raise TypeError("Loop must be a bool")
        elif not isinstance(curves, list):
            raise TypeError("Curves must be a list")
        else:
            self.duration = duration
            self.loop = loop
            self.curves = curves
            return

    def __str__(self):
        return f"Duration: {self.duration} - Loop: {self.loop} - Curves: {self.curves}"

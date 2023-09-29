from enum import Enum

######################## Main ########################
INSTRUMENT = 'Guitar'
STRING_NUM = 6
NOTE_PER_STRING = 22
OPEN_STRING_NOTE = {
    1:{'noteName':'E', 'pitchNum':4},
    2:{'noteName':'B', 'pitchNum':3},
    3:{'noteName':'G', 'pitchNum':3},
    4:{'noteName':'D', 'pitchNum':3},
    5:{'noteName':'A', 'pitchNum':2},
    6:{'noteName':'E', 'pitchNum':2},
}
HORIZON_LINES_INDEX_START = 1
HORIZON_LINES_INDEX_END = 132
VERTICAL_LINES_INDEX_START = 138
VERTICAL_LINES_INDEX_END = 252
POINTS_INDEX_START = 1
POINTS_INDEX_END = 132
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

class Mode(Enum):
    CHORD = 'Chord Mode'
    NOTE = 'Note Mode'

######################### UI #########################
WINDOW_SIZE = (1150, 600)

class ConstChordTextbox:
    X = 50
    startY = 160
    stepY = 40
    width = 42
    height = 32

class ConstHorizonLine:
    startX = 110
    stepX_1 = 60
    stepX_2 = 50
    stepX_3 = 40
    startY = 170
    stepY = 40
    width_1 = stepX_1 + 1
    width_2 = stepX_2 + 1
    width_3 = stepX_3 + 1
    height = 16

class ConstVerticalLine:
    startX = 100
    stepX_1 = 60
    stepX_2 = 50
    stepX_3 = 40
    startY = 180
    stepY = 40
    width = 16
    height = 41

class ConstPressPoint:
    startX = 130
    stepX_1 = 60
    stepX_2 = 55
    stepX_3 = 50
    stepX_4 = 45
    stepX_5 = 40
    startY = 170
    stepY = 40
    width = 21
    height = 21

class ConstMuteCheckBox:
    X = 20
    startY = 170
    stepY = 40
    width = 16
    height = 16
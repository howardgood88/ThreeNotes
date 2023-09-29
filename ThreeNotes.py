from PyQt5 import QtCore, QtGui, QtWidgets
from pychord import find_chords_from_notes
from pychord.analyzer import notes_to_positions
import Fretboard_ui
from const import *

class ThreeNotes(Fretboard_ui.Fretboard_ui): # Inherit from Fretboard_ui.py
    def __init__(self, MainWindow):
        super().__init__(MainWindow)
        # Get objects define in Fretboard_ui.py
        ## The notes now playing
        self.component_notes = {stringNum: val['noteName'] for stringNum, val in OPEN_STRING_NOTE.items()}
        ## The strings now muted
        self.string_muted = {i:False for i in range(1, STRING_NUM + 1)}
        self.Horizon_lines = [vars(self)[f'line_{i}'] for i in range(HORIZON_LINES_INDEX_START, HORIZON_LINES_INDEX_END + 1)]
        self.Vertical_lines = [vars(self)[f'line_{i}'] for i in range(VERTICAL_LINES_INDEX_START, VERTICAL_LINES_INDEX_END + 1)]
        self.points = [vars(self)[f'label_{i}'] for i in range(POINTS_INDEX_START, POINTS_INDEX_END + 1)]
        self.initLinkLinesAndPoints(self.Horizon_lines, self.points)
        self.strings = self.initString(self.Horizon_lines)
        self.textBrowsers = [vars(self)[f'textBrowser_{i}'] for i in range(1, STRING_NUM + 1)]
        self.checkBoxs = [vars(self)[f'checkBox_{i}'] for i in range(1, STRING_NUM + 1)]

        # Mode
        self.mode = Mode.CHORD
        self.initNoteMode()

        # init UI
        self.initAllNoteName()
        # QtCore.QMetaObject.connectSlotsByName(MainWindow)

        ## reset button / mode button event
        self.resetButton.clicked.connect(self.resetEvent)
        self.modeButton.clicked.connect(self.modeChangeEvent)
        ## mute check box event
        for i in range(STRING_NUM):
            self.checkBoxs[i].stateChanged.connect(self.selectCheckBoxEvent(stringNum = i + 1))

    ######################## Init ########################

    def initLinkLinesAndPoints(self, lines: list, points: list):
        '''
            Link lines and points, and init the press event.
        '''
        for line, point in zip(lines, points):
            point.mousePressEvent = self.pointPressEvent(point)
            point.press = False
            point.hide()

            line.point = point
            line.mousePressEvent = self.linePressEvent(line)

    def initString(self, lines: list):
        '''
            Pack every twelve continuously adjacent horizon lines into a string.
        '''
        class String(list):
            def __init__(self):
                super().__init__()
                self.pressedPoint = None
        strings = []
        for string_idx in range(STRING_NUM):
            strings.append(String())
            for note_idx in range(NOTE_PER_STRING):
                idx = string_idx * NOTE_PER_STRING + note_idx
                line = lines[idx]
                line.point.stringNum = string_idx + 1
                strings[-1].append(line)
        return strings

    def initNoteMode(self):
        '''
            Init note Mode.
        '''
        self.notes = {note : list() for note in NOTES}
        self.noteModePressedPoints = list()
        for point in self.points:
            self.notes[point.noteName].append(point)

    def initAllNoteName(self):
        '''
            Set the initial note name of each string.
        '''
        for string_idx in range(1, STRING_NUM+1):
            noteName = OPEN_STRING_NOTE[string_idx]['noteName']
            pitchNum = OPEN_STRING_NOTE[string_idx]['pitchNum']
            self.setNoteName(string_idx, noteName, pitchNum)

    ######################## Utility ########################

    def pointPress(self, point):
        '''
            The helper function for pressing on fret.
        '''
        stringNum = point.stringNum
        string = self.strings[stringNum - 1]
        if not point.press:
            if string.pressedPoint and self.mode == Mode.CHORD:
                string.pressedPoint.hide()
                string.pressedPoint.press = False
            string.pressedPoint = point
            point.show()
            point.press = True
            noteName, pitchNum = point.noteName, point.pitchNum
        else:
            point.hide()
            point.press = False
            string.pressedPoint = None
            noteName = OPEN_STRING_NOTE[stringNum]['noteName']
            pitchNum = OPEN_STRING_NOTE[stringNum]['pitchNum']
        self.component_notes[stringNum] = noteName
        self.setNoteName(stringNum, noteName, pitchNum)
        self.checkChord()

    def checkChord(self):
        '''
            Check the notes now playing from string six to string one, 
            sort by the distance to root note, and identify the chord by pychord.
        '''
        if self.mode == Mode.NOTE:    # Note Mode don't need to show chord
            return
        def getNotesPosition(component_notes: list, root_note):
            notes_position = notes_to_positions(component_notes, root_note)
            for idx in range(len(notes_position)):
                notes_position[idx] %= len(NOTES)       # 12 half steps a cycle
            return notes_position

        root_note = None
        component_notes = set()          # pychord cannot accept duplicate notes
        for idx in range(STRING_NUM, 0, -1):      # Order from string six to one to find root note
            if self.string_muted[idx]:
                continue
            if root_note == None:
                root_note = self.component_notes[idx]
            component_notes.add(self.component_notes[idx])
        component_notes = list(component_notes)
        notes_position = getNotesPosition(component_notes, root_note)

        _, component_notes = zip(*sorted(zip(notes_position, component_notes)))
        chord = find_chords_from_notes(component_notes)
        chordName = chord[0].chord if chord else ''
        self.setChordText(chordName)
        print(component_notes)
        print(chordName)
    
    def setChordText(self, chordName):
        '''
            Set the text in text browser by chord name.
        '''
        self.textBrowser_chord_identifier.setHtml("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
            "p, li { white-space: pre-wrap; }\n"
            "</style></head><body style=\" font-family:\'PMingLiU\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
            "<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">"
            f"<span style=\" font-weight:600;\">{chordName}</span></p></body></html>")

    def setNoteName(self, stringNum, noteName, pitchNum):
        '''
            Set the note of string "stringNum" by noteName and pitchNum.
        '''
        if self.mode == Mode.NOTE:      # Note Mode don't need to show pressed note name of the string
            return
        assert(0 < len(noteName) and len(noteName) < 3)
        s = f'{noteName[0]}'
        if len(noteName) == 2:
            s += f'<sup>{noteName[1]}</sup>'
        s += f'<sub>{pitchNum}</sub>'
        self.textBrowsers[stringNum-1].setHtml("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
            "p, li { white-space: pre-wrap; }\n"
            "</style></head><body style=\" font-family:\'PMingLiU\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
            "<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">"
            f"<span style=\" font-weight:600;\">{s}</span></p></body></html>")

    ######################## Event Handler ########################

    def pointPressEventHelper(self, point):
        '''
            Press the different points by mode.

            Chord mode: Press the single point.
            Note mode: Press all the same notes, even in different pitch.
        '''
        if self.mode == Mode.CHORD:
            self.pointPress(point)
        elif self.mode == Mode.NOTE:
            self.resetEvent()
            same_note_points = self.notes[point.noteName]
            self.noteModePressedPoints = same_note_points
            for same_note_point in same_note_points:
                self.pointPress(same_note_point)

    def linePressEvent(self, line):
        '''
            Press on the line.
        '''
        def linePressEventWrapper(e):
            point = line.point
            self.pointPressEventHelper(point)
        return linePressEventWrapper

    def pointPressEvent(self, point):
        '''
            Press on the showed point.
        '''
        def pointPressEventWrapper(e):
            self.pointPressEventHelper(point)
        return pointPressEventWrapper

    def resetEvent(self):
        '''
            Reset to original state.
        '''
        self.component_notes = {stringNum: val['noteName'] for stringNum, val in OPEN_STRING_NOTE.items()}
        if self.mode == Mode.CHORD:
            for string in self.strings:
                if string.pressedPoint != None:
                    point = string.pressedPoint
                    self.pointPress(point)
        elif self.mode == Mode.NOTE:
            for point in self.noteModePressedPoints:
                self.pointPress(point)
            self.noteModePressedPoints = list()
        for idx in range(STRING_NUM):
            if self.string_muted[idx + 1]:
                self.checkBoxs[idx].click()
        self.checkChord()

    def modeChangeEvent(self):
        '''
            Change between Chord Mode and Note Mode.
        '''
        self.resetEvent()
        if self.mode == Mode.CHORD:
            self.mode = Mode.NOTE
        elif self.mode == Mode.NOTE:
            self.mode = Mode.CHORD
        self.modeButton.setText(self.mode.value)

    def selectCheckBoxEvent(self, stringNum):
        '''
            Mute specific string.
        '''
        def selectCheckBoxEventWrapper():
            self.string_muted[stringNum] = not self.string_muted[stringNum]
            self.checkChord()
        return selectCheckBoxEventWrapper

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = ThreeNotes(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

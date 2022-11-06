from PyQt5 import QtCore, QtGui, QtWidgets
from pychord import find_chords_from_notes
from pychord.analyzer import notes_to_positions
import Fretboard_ui

INSTRUMENT = 'Guitar'
STRING_NUM = 6
NOTE_PER_STRING = 22
OPEN_STRING_NOTE_NAME = {
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
NOTES = {'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'}

class ThreeNotes(Fretboard_ui.Fretboard_ui): # Inherit from Fretboard_ui.py
    def __init__(self, MainWindow):
        '''
            The dynamic object: 
            self.component_notes: Record the notes now playing,
            self.string_muted: Record the strings now muting,
            self.strings[*].pressPoint: Record the point now pressing of string *,

            Point:
            self.strings[*][*].point, self.points[*], self.strings[*].pressPoint,
            self.Horizon_lines[*].point
        '''
        super().__init__(MainWindow)

        self.component_notes = {stringNum: val['noteName'] for stringNum, val in OPEN_STRING_NOTE_NAME.items()}
        self.string_muted = {i:False for i in range(1, STRING_NUM + 1)}
        self.Horizon_lines = [vars(self)[f'line_{i}'] for i in range(HORIZON_LINES_INDEX_START, HORIZON_LINES_INDEX_END + 1)]
        self.Vertical_lines = [vars(self)[f'line_{i}'] for i in range(VERTICAL_LINES_INDEX_START, VERTICAL_LINES_INDEX_END + 1)]
        self.points = [vars(self)[f'label_{i}'] for i in range(POINTS_INDEX_START, POINTS_INDEX_END + 1)]
        self.setRelationship(self.Horizon_lines, self.points)
        self.strings = self.string_init(self.Horizon_lines)
        self.textBrowsers = [vars(self)[f'textBrowser_{i}'] for i in range(1, STRING_NUM + 1)]
        self.checkBoxs = [vars(self)[f'checkBox_{i}'] for i in range(1, STRING_NUM + 1)]
        self.mode = 'Chord Mode'    # Chord Mode / Note Mode
        # Note Mode
        self.notes = {note : list() for note in NOTES}
        self.noteModePressedPoints = list()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # prepare reset and mode change button
        self.resetButton.clicked.connect(self.resetEvent)
        self.modeButton.clicked.connect(self.modeChangeEvent)

        # prepare mute check box
        def selectCheckBoxEvent(stringNum):
            self.string_muted[stringNum] = not self.string_muted[stringNum]
            self.checkChord()
        self.checkBoxs[0].stateChanged.connect(lambda:selectCheckBoxEvent(stringNum = 1))
        self.checkBoxs[1].stateChanged.connect(lambda:selectCheckBoxEvent(stringNum = 2))
        self.checkBoxs[2].stateChanged.connect(lambda:selectCheckBoxEvent(stringNum = 3))
        self.checkBoxs[3].stateChanged.connect(lambda:selectCheckBoxEvent(stringNum = 4))
        self.checkBoxs[4].stateChanged.connect(lambda:selectCheckBoxEvent(stringNum = 5))
        self.checkBoxs[5].stateChanged.connect(lambda:selectCheckBoxEvent(stringNum = 6))

        # append note to corresponding note list in self.notes
        for point in self.points:
            self.notes[point.noteName].append(point)

    def setRelationship(self, lines: list, points: list):
        '''
            Set the relationship between line and point and some initial values
        '''
        def mousePress_line(line):
            def mousePressEvent_dec(e):
                point = line.point
                if self.mode == 'Chord Mode':
                    self.pressPointHelper(point)
                else:   # Note Mode
                    self.resetEvent()
                    same_note_points = self.notes[point.noteName]
                    self.noteModePressedPoints = same_note_points
                    for same_note_point in same_note_points:
                        self.pressPointHelper(same_note_point)
            return mousePressEvent_dec

        def mousePress_point(point):
            def mousePressEvent_dec(e):
                if self.mode == 'Chord Mode':
                    self.pressPointHelper(point)
                else:   # Note Mode
                    self.resetEvent()
                    same_note_points = self.notes[point.noteName]
                    self.noteModePressedPoints = same_note_points
                    for same_note_point in same_note_points:
                        self.pressPointHelper(same_note_point)
            return mousePressEvent_dec

        for idx in range(len(lines)):
            line = lines[idx]
            point = points[idx]

            point.mousePressEvent = mousePress_point(point)
            point.press = False
            point.hide()

            line.point = point
            line.mousePressEvent = mousePress_line(line)

    def string_init(self, lines: list):
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

    def pressPointHelper(self, point):
        '''
            Set the reaction after pressing on fret.
        '''
        stringNum = point.stringNum
        string = self.strings[stringNum - 1]
        if not point.press:
            if string.pressedPoint and self.mode != 'Note Mode':
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
            noteName = OPEN_STRING_NOTE_NAME[stringNum]['noteName']
            pitchNum = OPEN_STRING_NOTE_NAME[stringNum]['pitchNum']
        self.component_notes[stringNum] = noteName
        self.setNoteName(stringNum, noteName, pitchNum)
        self.checkChord()

    def checkChord(self):
        '''
            Check the notes now playing from string six to string one, 
            sort by the distance to root note, and identify the chord by pychord.
        '''
        if self.mode == 'Note Mode':    # Note Mode don't need to show chord
            return
        def getNotesPosition(component_notes: list, root_note):
            notes_position = notes_to_positions(component_notes, root_note)
            for idx in range(len(notes_position)):
                notes_position[idx] %= 12       # 12 half steps a cycle
            return notes_position

        root_note = None
        component_notes = set()          # pychord cannot accept duplicate notes
        for idx in range(6, 0, -1):      # Order from string six to one to find root note
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
        _translate = QtCore.QCoreApplication.translate
        self.textBrowser_chord_identifier.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
            "p, li { white-space: pre-wrap; }\n"
            "</style></head><body style=\" font-family:\'PMingLiU\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
            f"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">{chordName}</span></p></body></html>"))

    def retranslateUi(self, MainWindow):
        '''
            Set the initial text of all object.
        '''
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "ThreeNotes"))
        for string_idx in range(1, STRING_NUM+1):
            noteName = OPEN_STRING_NOTE_NAME[string_idx]['noteName']
            pitchNum = OPEN_STRING_NOTE_NAME[string_idx]['pitchNum']
            self.setNoteName(string_idx, noteName, pitchNum)
        self.label_200.setText(_translate("MainWindow", "3"))
        self.label_201.setText(_translate("MainWindow", "5"))
        self.label_202.setText(_translate("MainWindow", "7"))
        self.label_203.setText(_translate("MainWindow", "9"))
        self.label_204.setText(_translate("MainWindow", "12"))
        self.label_205.setText(_translate("MainWindow", "15"))
        self.label_206.setText(_translate("MainWindow", "17"))
        self.label_207.setText(_translate("MainWindow", "19"))
        self.label_208.setText(_translate("MainWindow", "21"))
        self.label_chord_identifier.setText(_translate("MainWindow", "Chord:"))
        self.label_check_box.setText(_translate("MainWindow", "Mute"))
        self.resetButton.setText(_translate("MainWindow", "Reset"))
        self.modeButton.setText(_translate("MainWindow", "Chord Mode"))

    def setNoteName(self, stringNum, noteName, pitchNum):
        '''
            Set the note of string "stringNum" by noteName and pitchNum.
        '''
        if self.mode == 'Note Mode':
            return
        assert(0 < len(noteName) and len(noteName) < 3)
        s = f'{noteName[0]}'
        if len(noteName) == 2:
            s += f'<sup>{noteName[1]}</sup>'
        s += f'<sub>{pitchNum}</sub>'
        _translate = QtCore.QCoreApplication.translate
        self.textBrowsers[stringNum-1].setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
    "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
    "p, li { white-space: pre-wrap; }\n"
    "</style></head><body style=\" font-family:\'PMingLiU\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
    f"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">{s}</span></p></body></html>"))

    def resetEvent(self):
        '''
            Reset to original state.
        '''
        self.component_notes = {stringNum: val['noteName'] for stringNum, val in OPEN_STRING_NOTE_NAME.items()}
        if self.mode == 'Chord Mode':
            for string in self.strings:
                if string.pressedPoint != None:
                    point = string.pressedPoint
                    self.pressPointHelper(point)
        else:   # Note Mode
            for point in self.noteModePressedPoints:
                self.pressPointHelper(point)
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
        _translate = QtCore.QCoreApplication.translate
        if self.mode == 'Chord Mode':   # to Note Mode
            self.mode = 'Note Mode'
        else:   # to Chord Mode
            self.mode = 'Chord Mode'
        self.modeButton.setText(_translate("MainWindow", self.mode))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = ThreeNotes(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

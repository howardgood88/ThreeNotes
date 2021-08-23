from PyQt5 import QtCore, QtGui, QtWidgets
from pychord import note_to_chord
from pychord.analyzer import notes_to_positions
import Fretboard_ui

INSTRUMENT = 'Guitar'
STRING_NUM = 6
NOTE_PER_STRING = 12
OPEN_STRING_NOTE_NAME = {
    1:{'noteName':'E', 'pitchNum':4},
    2:{'noteName':'B', 'pitchNum':3},
    3:{'noteName':'G', 'pitchNum':3},
    4:{'noteName':'D', 'pitchNum':3},
    5:{'noteName':'A', 'pitchNum':2},
    6:{'noteName':'E', 'pitchNum':2},
}
HORIZON_LINES_INDEX_START = 1
HORIZON_LINES_INDEX_END = 72
VERTICAL_LINES_INDEX_START = 138
VERTICAL_LINES_INDEX_END = 202
POINTS_INDEX_START = 1
POINTS_INDEX_END = 72


class ThreeNotes(Fretboard_ui.Fretboard_ui): # Inherit from Fretboard_ui.py
    def __init__(self, MainWindow):
        super().__init__(MainWindow)

        self.component_notes = {
            1:'E', 2:'B', 3:'G',
            4:'D', 5:'A', 6:'E'
        }
        self.string_muted = {i:False for i in range(1, STRING_NUM + 1)}
        self.Horizon_lines = [vars(self)[f'line_{i}'] for i in range(HORIZON_LINES_INDEX_START, HORIZON_LINES_INDEX_END + 1)]
        self.Vertical_lines = [vars(self)[f'line_{i}'] for i in range(VERTICAL_LINES_INDEX_START, VERTICAL_LINES_INDEX_END + 1)]
        self.points = [vars(self)[f'label_{i}'] for i in range(POINTS_INDEX_START, POINTS_INDEX_END + 1)]
        self.setRelationship(self.Horizon_lines, self.points)
        self.strings = self.string_init(self.Horizon_lines)
        self.textBrowsers = [vars(self)[f'textBrowser_{i}'] for i in range(1, STRING_NUM + 1)]

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def setRelationship(self, lines, points):
        '''
            Set the relationship between line and point and some initial values
        '''
        def mousePress_line(line):
            def mousePressEvent_dec(e):
                point = line.point
                self.pressPointHelper(point)
            return mousePressEvent_dec

        def mousePress_point(point):
            def mousePressEvent_dec(e):
                self.pressPointHelper(point)
            return mousePressEvent_dec

        for idx in range(len(lines)):
            line = lines[idx]
            point = points[idx]

            point.mousePressEvent = mousePress_point(point)
            point.press = False
            point.lock = False
            point.hide()

            line.point = point
            line.mousePressEvent = mousePress_line(line)

    def string_init(self, lines):
        '''
            Pack every twelve continuously adjacent horizon lines into a string.
        '''
        class String(list):
            def __init__(self):
                super().__init__()
                self.pressedPoint = None
        strings = String()
        for string_idx in range(STRING_NUM):
            strings.append([])
            for note_idx in range(NOTE_PER_STRING):
                idx = string_idx * NOTE_PER_STRING + note_idx
                assert(0 <= idx and idx < 72)
                line = lines[idx]
                line.point.stringNum = string_idx + 1
                strings[-1].append(line)
        return strings

    def pressPointHelper(self, point):
        '''
            Set the reaction after pressing on fret.
        '''
        if point.lock:
            return
        if not point.press:
            self.strings.pressedPoint = point
            point.show()
            point.press = True
            self.component_notes[point.stringNum] = point.noteName
            self.setNoteName(point.stringNum, point.noteName, point.pitchNum)
            # Lock other frets in the same string
            for line in self.strings[point.stringNum-1]:
                point_ = line.point
                if point_ != point:
                    point_.lock = True
                    line.setCursor(QtGui.QCursor(QtCore.Qt.ForbiddenCursor))
        else:
            point.hide()
            point.press = False
            noteName = OPEN_STRING_NOTE_NAME[point.stringNum]['noteName']
            pitchNum = OPEN_STRING_NOTE_NAME[point.stringNum]['pitchNum']
            self.component_notes[point.stringNum] = noteName
            self.setNoteName(point.stringNum, noteName, pitchNum)
            for line in self.strings[point.stringNum-1]:
                line.point.lock = False
                line.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.checkChord()

    def checkChord(self):
        '''
            Check the notes now playing from string six to string one, 
            sort by the distance to root note, and identify the chord by pychord.
        '''
        def getNotesPosition(component_notes: list, root_note):
            notes_position = notes_to_positions(component_notes, root_note)
            for idx in range(len(notes_position)):
                notes_position[idx] %= 12       # 12 half steps a cycle
            return notes_position

        root_note = None
        component_notes = set()          # pychord cannot accept duplicate notes.
        for idx in range(6, 0, -1):      # Order from string six to one to find root note.
            if self.string_muted[idx]:
                continue
            if root_note == None:
                root_note = self.component_notes[idx]
            component_notes.add(self.component_notes[idx])
        component_notes = list(component_notes)
        notes_position = getNotesPosition(component_notes, root_note)

        _, component_notes = zip(*sorted(zip(notes_position, component_notes)))
        Chord = note_to_chord(component_notes)
        Chord = Chord[0].chord if Chord else ''
        self.setChord(Chord)
        print(component_notes)
        print(Chord)
    
    def setChord(self, chord):
        _translate = QtCore.QCoreApplication.translate
        self.textBrowser_chord_identifier.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
            "p, li { white-space: pre-wrap; }\n"
            "</style></head><body style=\" font-family:\'PMingLiU\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
            f"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">{chord}</span></p></body></html>"))

    def retranslateUi(self, MainWindow):
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
        self.label_chord_identifier.setText(_translate("MainWindow", "Chord:"))
        self.label_check_box.setText(_translate("MainWindow", "Mute"))

    def setNoteName(self, stringNum, noteName, pitchNum):
        assert(len(noteName) < 3 and len(noteName) > 0)
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
        

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = ThreeNotes(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

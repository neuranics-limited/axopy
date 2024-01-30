#this may need to be split up a bit later
import sys
import os
from PyQt5 import QtCore, QtWidgets, QtGui
import collections
from .main import get_qtapp

def show_yes_no_dialog(text: str, informativeText: str = "") -> bool:
    """ Dialog which prompts the user to either agree or disagree
    
    primarily to be used to confirm if the user wants to continue with a given process or stop
    
    Arguments
    ---------
    text - a string to describe the main reason for the dialog
    informativeText - a string to add more details 
    
    Returns
    --------
    bool - True for yes, False for no
    """
    app = get_qtapp() #to ensure the app has been initialized
    msgBox = QtWidgets.QMessageBox()
    msgBox.setWindowTitle("Dialog")
    msgBox.setWindowIcon(QtGui.QIcon(":/icons/logo_small.png"))
    msgBox.setText(text)
    msgBox.setInformativeText(informativeText)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    
    returnValue = msgBox.exec()
    if returnValue == QtWidgets.QMessageBox.Yes:
        return True
    else:
        return False

def check_subject_id_exists(root: str, subject: str) -> bool:
        """Check if given subject name already exists and should not be used

        Returns
        -------
        bool: True if the given subject id already exists 
        """
        try:
            ls = os.listdir(root)
        except:
            return False
        else:
            for name in sorted(ls):
                path = os.path.join(root, name)
                if os.path.isdir(path) and subject==name:
                    return True
            return False

def check_if_invalid_filename(subject: str) -> bool:
    """ Check if given string is a valid filename and does not contain illegal symbols
    Returns
    -------
    bool: if the filename is invalid
    """
    illegalSymbols = ["#", "%", "&", "{","}","\\",">","<", "*", "?", "/", "$", "!", "'", '"',"@", "+", "`", "|", "="]
    
    if len(subject)>=31:
        return True #filename is too long
    
    return any(char in subject for char in illegalSymbols)
        


class ConfigureSubjectName(QtWidgets.QDialog):
    """Based on _SessionConfig: Widget for configuring a session.
    

    Shows a form layout with the specified options. Options are passed as a
    dictionary with option labels as keys and option types as values. The value
    can also be a sequence of strings, which are shown in a combo box. Use
    ``run()`` to run the dialog and return the results in a dictionary.

    Arguments
    ---------
    root - the root directory for savig the data
    
    Returns
    -------
    results - the subject as part of a dictionary {'subject':}
    """

    def __init__(self, root, taskName: str = ""):
        app = get_qtapp()
        super(ConfigureSubjectName, self).__init__()
        self.options = {"subject" : str}
        if taskName != "Demo":
            self.options["duration"] = float
        self.results = {}
        self.widgets = {}
        self.root = root

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setFormAlignment(QtCore.Qt.AlignVCenter)
        main_layout.addLayout(form_layout)
        self.setWindowTitle("Setup")
        self.setWindowIcon(QtGui.QIcon(":/icons/logo_small.png"))

        for label, typ in self.options.items():
            if label == "duration":
                w = QtWidgets.QDoubleSpinBox()
                w.setRange(1,60)
                w.setDecimals(1)
                w.setSingleStep(1.0)
                w.setSuffix(" min")
                if taskName == "Oscilloscope": w.setValue(10.0)
                else: w.setValue(1.0)
                self.widgets[label] = w
                form_layout.addRow(label, w)
            elif typ in {str, int, float}:
                w = QtWidgets.QLineEdit()
                self.widgets[label] = w
                if label =="subject":
                    form_layout.addRow("file name", w)
                else:
                    form_layout.addRow(label, w)
            elif isinstance(typ, collections.abc.Sequence):
                w = QtWidgets.QComboBox()
                for choice in typ:
                    w.addItem(str(choice))
                self.widgets[label] = w
                form_layout.addRow(label, w)
            else:
                raise TypeError("option {} ({}) not a supported type".format(
                    label, typ))

        button = QtWidgets.QPushButton("Ok")
        main_layout.addWidget(button)
        button.clicked.connect(self._on_button_click)

        self.show()

    def run(self):
        self.exec_()
        return self.results

    def _on_button_click(self):
        for label, widget in self.widgets.items():
            t = self.options[label]
            if t is str:
                self.results[label] = str(widget.text())
            elif t is int:
                self.results[label] = int(widget.text())
            elif t is float:
                parts = widget.text().split(" ")
                self.results[label] = float(parts[0])
            else:
                self.results[label] = str(widget.currentText())
        
        if 'subject' in self.options:
            if self.results['subject'][0] in [" ", "_", "-", "."]:
                self.results['subject'] = self.results['subject'][1:]
            for char in reversed(self.results['subject']):
                if char == " ":
                    self.results['subject'] = self.results['subject'][:-1]
                else:
                    break

        if 'subject' in self.options and self.results['subject'] == '':
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Subject ID must not be empty.",
                QtWidgets.QMessageBox.Ok)
            return
        elif check_if_invalid_filename(self.results['subject']):
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Invalid file name. Please ensure the name is less than 31 characters and does not contain any of these symbols: #%&{}\\><*?",
                QtWidgets.QMessageBox.Ok)
            self.results["subject"] = ""
            return
        elif check_subject_id_exists(self.root, self.results['subject']):
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Subject ID already exists.",
                QtWidgets.QMessageBox.Ok)
            return
        
        self.done(0)

       
   
class SelectorDialog(QtWidgets.QDialog):
    """ Dialog to ask the user to select an option from list supplied from a dictionary
    use run() to run the dialog and return the results in a dictionary
    
    Arguments
    ---------
    text - a message string to explain the purpose of the dialog
    options - a dictionary containing the selections in a list 
    informativeText - a message to further explain the purpose of the dialog
    
    Returns
    -------
    result - string of the chosen option
    """
    def __init__(self, text: str, options: dict, informativeText: str = "") -> None:
        app = get_qtapp()
        super(SelectorDialog, self).__init__()
        self.options = options
        self.result = None
        
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        
        #need to add title and informative text to the widget 
        main_layout.addWidget(QtWidgets.QLabel(text))
        main_layout.addWidget(QtWidgets.QLabel(informativeText))
        
        form_layout = QtWidgets.QFormLayout()
        form_layout.setFormAlignment(QtCore.Qt.AlignVCenter)
        main_layout.addLayout(form_layout)
        
        self.setWindowTitle("Setup")
        self.setWindowIcon(QtGui.QIcon(":/icons/logo_small.png"))
        


        for label, typ in self.options.items():
            if isinstance(typ, collections.abc.Sequence):
                self.widget = QtWidgets.QComboBox()
                for choice in typ:
                    self.widget.addItem(str(choice))
                form_layout.addRow(label, self.widget)
            else:
                raise TypeError("option {}({}) not a supported type".format(
                    label, typ))
        
        button = QtWidgets.QPushButton("Confirm")
        main_layout.addWidget(button)
        button.clicked.connect(self._on_ok_button_click)
        
        self.show()

    def run(self) -> str:
        self.exec_()
        return self.result
    
    def _on_ok_button_click(self) -> None:
        #this needs to set self.result to properly return the correct information 
        self.result = str(self.widget.currentText())
        self.done(0)
            
class SessionSetup(QtWidgets.QDialog):
    """
    this is for displaying the connection options to the user and handling any connections to devices (esp. BLE devices).
    The user can also use this to select the task they want to run 
    
    In the future, this would not have the user option, but would rather 
    automatically connect to the designated device
    
    Arguments
    ---------
    
    Returns
    -------
    results - dict with the options chosen by the user
    
    Notes
    -----
    
    """

    #this should be its own window with mutliple options
    def __init__(self):
        app = get_qtapp()
        super(SessionSetup, self).__init__()
        self.widgets = {}
        self.results = {}
        
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        
        self.setWindowTitle("Setup")
        self.setWindowIcon(QtGui.QIcon(":/icons/logo_small.png"))
        
        #Add text:
        self.widgets["text"] = QtWidgets.QLabel("Please select the options for the experimental setup:")
        main_layout.addWidget(self.widgets["text"])
        
        
        daq_form_layout = QtWidgets.QFormLayout()
        daq_form_layout.setFormAlignment(QtCore.Qt.AlignVCenter)
        main_layout.addLayout(daq_form_layout)
        
        #in both cases the format is {type:description}
        self.daqOptions = {"Bluetooth": "A wireless connection using BLE protocols with a sampling rate of 640 samples/second", 
                            "Wired XCG": "Connected to the computer via USB with a sampling rate of 640 samples/second",
                            "Wired MCG": "Connected to the computer via USB with a sampling rate of 640 samples/second",
                            "Noise": "Randomly generated data"
                            }
        self.widgets["daq"] = QtWidgets.QComboBox()
        for daq in self.daqOptions:
            self.widgets["daq"].addItem(daq)
        daq_form_layout.addRow("DAQ options:", self.widgets["daq"])
        
        self.widgets["daq_desc"] = QtWidgets.QLabel(self.daqOptions[self.widgets["daq"].currentText()])
        self.widgets["daq"].currentIndexChanged.connect(self.selections_changed)
        main_layout.addWidget(self.widgets["daq_desc"])
        
        task_form_layout = QtWidgets.QFormLayout()
        task_form_layout.setFormAlignment(QtCore.Qt.AlignVCenter)
        main_layout.addLayout(task_form_layout)

        self.taskOptions = {"Demo": "Displays the raw signal from the DAQ", 
                       "Oscilloscope": "Displays and saves the raw signal from the DAQ",
                       "MCG Recording": "Receives the siganl from the DAQ and applying processing for relevant features",
                       }
        self.widgets["task"] = QtWidgets.QComboBox()
        for task in self.taskOptions:
            self.widgets["task"].addItem(task)
        task_form_layout.addRow("Experiment:", self.widgets["task"])

        self.widgets["task_desc"] = QtWidgets.QLabel(self.taskOptions[self.widgets["task"].currentText()])
        self.widgets["task"].currentIndexChanged.connect(self.selections_changed)
        main_layout.addWidget(self.widgets["task_desc"])
        


        button = QtWidgets.QPushButton("Ok")
        main_layout.addWidget(button)
        button.clicked.connect(self._on_ok_button_click)

        self.show()

    def selections_changed(self, newIndex:int) -> None:
        self.widgets["task_desc"].setText(self.taskOptions[self.widgets["task"].currentText()])
        self.widgets["daq_desc"].setText(self.daqOptions[self.widgets["daq"].currentText()])
        
    def run(self) -> dict:
        self.exec_()
        return self.results
    
    def _on_ok_button_click(self) -> None:
        for label, widget in self.widgets.items():
            if type(widget) is QtWidgets.QComboBox:
                self.results[label] = str(widget.currentText())
        
        self.done(0)
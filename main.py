import sys, os
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QFileDialog
from PyQt5 import uic
from PyQt5.QtGui import QIcon
import json
from cryptography import fernet
import threading
import tempfile
import zipfile
from bin.plugins import gpkg_reader as g_r
from bin.plugins import img_source
import shutil

# Temp Folder
def temp_mk(folder):
    x = tempfile.gettempdir() + '\\' + folder
    if os.path.exists(x):
        return
    else:
        os.mkdir(x)

def temp_get(folder):
    return tempfile.gettempdir() + '\\' + folder

def temp_rem(folder):
    shutil.rmtree(tempfile.gettempdir() + '\\' + folder + "\\")
# Json
def _json_read(jsoncontent, is_file=False):
    if is_file:
        content = open(jsoncontent, 'r').read()
    else:
        content = jsoncontent
    return json.loads(content)

# Config gpkg's
config_file_content = open('bin/project.gpkg', 'rb').read()
config_file_content = g_r.read(config_file_content)

version_file_content = open('bin/version.gpkg', 'rb').read()
version_file_content = g_r.read(version_file_content)

CONFIG = _json_read(config_file_content)
RESOURCES = CONFIG['$resources']
VERSION = _json_read(version_file_content)

TEMPDIR_NAME = ".$cpunwrapper"

temp_mk(TEMPDIR_NAME)

TEMPDIR = temp_get(TEMPDIR_NAME) + '\\'

# UI
class MainApp(QMainWindow, QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(RESOURCES['ui'][0], self)  # ui file load
        self.setWindowIcon(QIcon())  # Icon Loading

        self.interaction_list = [
            self.btn_browse,
            self.btn_browse_key,
            self.btn_start,
            self.rad_unwrap,
            self.rad_wrap,
            self.line_path,
            self.line_path_key
        ]

        self._REFRESH_HEAD()
        self._radio_change()

        self.btn_browse.clicked.connect(self._browse)
        self.btn_browse_key.clicked.connect(self._browse_key)
        self.btn_start.clicked.connect(self._startTh)

        self.btn_github.clicked.connect(self.send_to_github)
        
        self.rad_unwrap.toggled.connect(self._radio_change)
        self.rad_wrap.toggled.connect(self._radio_change)
    

    def interaction_disable(self):
        for action in self.interaction_list:
            action.setEnabled(False)
    def interaction_enable(self):
        for action in self.interaction_list:
            action.setEnabled(True)

    def send_to_github(self):
        import webbrowser
        webbrowser.open_new_tab('https://github.com/qwertzuiii')

    def _radio_change(self):
        if self.rad_wrap.isChecked():
            self.line_path.setPlaceholderText("Path to Wrap (.zip)")
        else:
            self.line_path.setPlaceholderText("Path to Unwrap (.cp)")

    def _REFRESH_HEAD(self):
        self.label_headline.setText(CONFIG['project_name'])
        self.label_version.setText("version {} ({}), by {}".format(VERSION['version'], VERSION['buildnum'], CONFIG['project_creator']))
    
    def _browse(self):
        if self.rad_wrap.isChecked():
            filter = "Zip Package (*.zip);;Content Package (*.cp);;Any Files (*)"
        else:
            filter = "Content Package (*.cp);;Zip Package (*.zip);;Any Files (*)"
        dir = QFileDialog.getOpenFileName(caption="Open a .cp file", filter=filter)
        
        if dir[0] != "":
            self.line_path.setText(dir[0])
        else:
            print('Operation cancelled')
    
    def _browse_key(self):
        dir = QFileDialog.getOpenFileName(caption="Open a .cp_key file", filter="Content Package Key (*.cp_key);;Any Files (*)")
        
        if dir[0] != "":
            self.line_path_key.setText(dir[0])
        else:
            print('Operation cancelled')

    def _startTh(self):
        if self.rad_unwrap.isChecked():
            target = self.start_unwrap
        elif self.rad_wrap.isChecked():
            target = self.start_wrap
        
        self.interaction_disable()

        x = threading.Thread(target=target)
        x.start()

    
    def start_unwrap(self):
        path_file = self.line_path.text()
        path_key  = self.line_path_key.text()

        if path_file == "":
            print('Operation cancelled: File Path is empty')
            return self.interaction_enable()
        
        output_folder_split = path_file.split('/')
        output_folder = ""
        output_folder_len = len(output_folder_split) - 1

        for i in range(output_folder_len):
            output_folder += output_folder_split[i] + '/'
        
        output_folder += "UNWRAP_" + output_folder_split[output_folder_len]

        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        else:
            os.mkdir(output_folder)
        
        print(output_folder)

        if path_key == "":
            cont_key = RESOURCES['base_key']
            cont_key = cont_key.encode()
        else:
            cont_key = open(path_key, 'rb').read()

        fer = fernet.Fernet(cont_key)

        with open(path_file, 'rb') as f:
            file_content = f.read()
        
        with open(TEMPDIR + "unwrap.temp", 'wb') as wr:
            wr.write(fer.decrypt(file_content))

        with zipfile.ZipFile(TEMPDIR + "unwrap.temp", 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        
        os.remove(TEMPDIR + "unwrap.temp")

        print('Finished')
        self.interaction_enable()
    
    def start_wrap(self):
        path_file = self.line_path.text()
        path_key  = self.line_path_key.text()

        if path_file == "":
            print('Operation cancelled: File Path is empty')
            return self.interaction_enable()
        
        output_folder_split = path_file.split('/')
        output_folder = ""
        output_folder_len = len(output_folder_split) - 1

        for i in range(output_folder_len):
            output_folder += output_folder_split[i] + '/'
        
        output_folder += output_folder_split[output_folder_len] + ".cp"
        
        print(output_folder)

        if path_key == "":
            cont_key = RESOURCES['base_key']
            cont_key = cont_key.encode()
        else:
            cont_key = open(path_key, 'rb').read()

        fer = fernet.Fernet(cont_key)

        with open(path_file, 'rb') as f:
            file_content = f.read()
        
        with open(output_folder, 'wb') as wr:
            wr.write(fer.encrypt(file_content))

        print('Finished')
        self.interaction_enable()

if __name__ == '__main__':

    if "--generate_key" in sys.argv:
        x = fernet.Fernet.generate_key()
        print('KEY:', x.decode())
        sys.exit()

    app = QApplication(sys.argv)
    appMain = MainApp()
    appMain.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print('Exiting...')
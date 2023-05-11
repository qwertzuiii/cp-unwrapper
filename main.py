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

        self._REFRESH_HEAD()

        self.btn_browse.clicked.connect(self._browse)
        self.btn_browse_key.clicked.connect(self._browse_key)
        self.btn_start.clicked.connect(self._startTh)
        self.btn_start_wrap.clicked.connect(self._startWrTh)

    def _REFRESH_HEAD(self):
        self.label_headline.setText(CONFIG['project_name'])
        self.label_version.setText("version {} ({}), by {}".format(VERSION['version'], VERSION['buildnum'], CONFIG['project_creator']))
    
    def _browse(self):
        dir = QFileDialog.getOpenFileName(caption="Open a .cp file", filter="Content Package (*.cp);;Any Files (*)")
        
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
        x = threading.Thread(target=self.start_unwrap)
        x.start()
    
    def _startWrTh(self):
        x = threading.Thread(target=self.start_wrap)
        x.start()
    
    def start_unwrap(self):
        path_file = self.line_path.text()
        path_key  = self.line_path_key.text()

        if path_file == "":
            print('Operation cancelled: File Path is empty')
            return
        
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
    
    def start_wrap(self):
        path_file = self.line_path.text()
        path_key  = self.line_path_key.text()

        if path_file == "":
            print('Operation cancelled: File Path is empty')
            return
        
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

if __name__ == '__main__':

    if "--generatekey" in sys.argv:
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
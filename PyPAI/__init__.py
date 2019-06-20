import PyQt5 as qt
import PyQt5.QtWidgets as ws
import PyQt5.QtGui as gui
import PyQt5.QtCore as core
import subprocess as sub
from sys import path
import os.path
import requests
from bs4 import BeautifulSoup as soup
from threading import Thread
from webbrowser import open_new_tab

class Pip:
    def __init__(self, path=''):
        self.path = path
    def install(self, name):
        python = os.path.join(self.path,'python.exe')
        com = sub.Popen([python,'-m','pip','install',name],stdout=sub.PIPE,shell=True)
        output = com.stdout.readlines()
        ret = []
        c = 0
        for i in output:
            if type(i) == bytes:
                if c>1:
                    ret.append(str(i)[2:len(i)])
                c += 1
        return ret
    def uninstall(self, name):
        python = os.path.join(self.path,'python.exe')
        com = sub.Popen([python,'-m','pip','uninstall',name,'-y'],stdout=sub.PIPE,shell=True)
        output = com.stdout.readlines()
        ret = []
        c = 0
        for i in output:
            if type(i) == bytes:
                if c>1:
                    ret.append(str(i)[2:len(i)])
                c += 1
        return ret
    def plist(self,versions=True):
        python = os.path.join(self.path,'python.exe')
        com = sub.Popen([python,'-m','pip','list'],stdout=sub.PIPE,shell=True)
        output = com.stdout.readlines()
        ret = []
        c = 0
        for i in output:
            if type(i) == bytes:
                if c>1:
                    if versions:
                        parts = i.split()
                        ret.append(str(parts[0] + b' v' + parts[1]))
                    else:
                        part = str(i)[2:len(i)]
                        parts = part.split()
                        ret.append(parts[0])
                c += 1
        return ret
#---------------------------------------------------
class App:
    def setPythonVersion(self):
        possible = list(map(str,[2,2.3,2.4,2.5,2.6,2.7,3,3.0,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.8]))
        possible.append('All')
        selection = ws.QInputDialog.getItem(
            self.mainWidget,
            'Set Python Version',
            'Select the python version to filter for.',
            possible,
            current=possible.index(self.version)
            )
        if selection[1]:
            self.version = selection[0]
        self.update()
        
    def setPipPath(self):
        path = ws.QFileDialog.getExistingDirectory(caption='Select python.exe folder')
        if not path == '':
            self.pipPath = path
        self.pip = Pip(path=self.pipPath)
    def installun(self):
        if not self.selected in self.pip.plist(versions=False):
            msg = ws.QMessageBox(1,'Install Complete','\n'.join(list(map(str,self.pip.install(self.selected)))))
            msg.exec_()
        else:
            self.pip.uninstall(self.selected)
            msg = ws.QMessageBox(1,'Uninstall Complete','Successfully uninstalled '+self.selected)
            msg.exec_()
    def search(self):
        self.searchStr = self.searchBox.text()
        self.update()
    def seePage(self):
        open_new_tab('https://pypi.org/project/'+self.selected)
    def modClicked(self,item):
        self.selected = item.text()
    def update(self):
        if len(self.searchStr) == 0:
            return
        self.results = []
        reqParams = {'q':self.searchStr,'c':'Programming Language :: Python :: '+self.version}
        if self.version == 'All':
            del reqParams['c']
        r = requests.get('https://pypi.org/search/',params=reqParams)
        tempsoup = soup(r.text,features="html.parser")
        print(r.url)
        try:
            pages = tempsoup.select('.button.button-group__button')
            pages = int(pages[len(pages)-2].string)
            for n in range(1,pages+1):
                reqParams = {'q':self.searchStr,'c':'Programming Language :: Python :: '+self.version,'page':n}
                if self.version == 'All':
                    del reqParams['c']
                r = requests.get('https://pypi.org/search/',params=reqParams)
                if r.status_code == 404:
                    break
                tempsoup = soup(r.text,features="html.parser")
                packs = tempsoup.select('.package-snippet__name')
                for i in packs:
                    #print(i.string)
                    self.results.append(i.string)
                self.progressBar.setValue((n/pages)*100)
                self.progressBar.show()
                
                

        except IndexError:
            reqParams = {'q':self.searchStr,'c':'Programming Language :: Python :: '+self.version}
            r = requests.get('https://pypi.org/search/',params=reqParams)
            tempsoup = soup(r.text,features="html.parser")
            packs = tempsoup.select('.package-snippet__name')
            for i in packs:
                #print(i.string)
                self.results.append(i.string)
        #self.results.sort()
        self.listWidget.clear()
        self.listWidget.addItems(self.results)
        self.listWidget.show()
        self.progressBar.setValue(0)
        self.progressBar.show()

    def __init__(self):
        #setup vars
        self.results = []
        self.selected = None
        self.searchStr = ''
        self.pip = Pip()
        self.version = 'All'
        self.pipPath = ''
        
        #setup gui
        self.app = ws.QApplication([])
        self.window = ws.QMainWindow()
        self.window.setMinimumSize(500,500)
        self.window.setWindowTitle('PyPAI - Python Package Automated Installer')
        self.window.setWindowIcon(gui.QIcon('icon.ico'))
        
        #make dock widget
        self.dock = ws.QMenuBar()

        #make pref menu
        self.PrefMenu = ws.QMenu()
        self.PrefMenu.setTitle('Preferences')
        self.PrefVersion = self.PrefMenu.addAction('Set Python Version')
        self.PrefVersion.triggered.connect(self.setPythonVersion)
        self.PipPath = self.PrefMenu.addAction('Set Python Path')
        self.PipPath.triggered.connect(self.setPipPath)

        #set dock
        self.dock.addMenu(self.PrefMenu)
        self.window.setMenuBar(self.dock)

        #main widget
        self.mainLayout = ws.QVBoxLayout()
        self.searchBar = ws.QHBoxLayout()
        self.actBar = ws.QHBoxLayout()

        #search bar
        self.searchBox = ws.QLineEdit()
        self.searchBox.setPlaceholderText('Search')
        self.searchBox.returnPressed.connect(self.search)
        self.searchButton = ws.QPushButton('Search')
        self.searchButton.pressed.connect(self.search)
        self.refresh = ws.QPushButton(gui.QIcon('refresh.png'),'')
        self.refresh.pressed.connect(self.update)
        self.searchBar.addWidget(self.searchBox)
        self.searchBar.addWidget(self.searchButton)
        self.searchBar.addWidget(self.refresh)
        self.mainLayout.addLayout(self.searchBar)

        #result table
        self.listWidget = ws.QListWidget()
        self.listWidget.itemClicked.connect(self.modClicked)
        self.mainLayout.addWidget(self.listWidget)

        #action buttons
        self.buttonBar = ws.QHBoxLayout()
        self.installUn = ws.QPushButton('Install/Uninstall')
        self.installUn.pressed.connect(self.installun)
        self.seePageButton = ws.QPushButton('See Page')
        self.seePageButton.pressed.connect(self.seePage)
        self.buttonBar.addWidget(self.installUn)
        self.buttonBar.addWidget(self.seePageButton)
        self.mainLayout.addLayout(self.buttonBar)

        #progress bar
        self.progressBar = ws.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.mainLayout.addWidget(self.progressBar)

        self.mainWidget = ws.QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.window.setCentralWidget(self.mainWidget)
        self.window.show()
        self.app.exec_()

App()

#!python

from typing import Dict
import sys
import json
import pathlib
from PyQt5.QtCore import QUrl, Qt, pyqtSignal, QTimer, QByteArray
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QSlider, QVBoxLayout, QFileDialog, QScrollArea
from PyQt5.QtGui import QIcon, QPixmap


# 静态全局配置
DEFAULT_CONFIG = pathlib.Path.home() / ".wmask"
DEFAULT_FOLDER_PATH = ""
DEFAULT_VOLUME = 30
DEFAULT_OPACITY = 20
DEFAULT_PLAY = False
DEFAULT_ACTIVE = False


# 应用主界面
class WmaskMain(QMainWindow):
    def __init__(self):
        super().__init__()
        # 全局参数
        self.folder_path = DEFAULT_FOLDER_PATH
        self.default_volume = DEFAULT_VOLUME
        self.default_opacity = DEFAULT_OPACITY
        self.default_play = DEFAULT_PLAY
        self.default_active = DEFAULT_ACTIVE
        # 主界面保持的数据
        self.playlist = set() # 媒体路径
        self.positions: Dict[str, int] = dict() # 媒体路径->进度
        self.volumes: Dict[str, int] = dict() # 媒体路径->音量(max:100)
        self.opacitys: Dict[str, int] = dict() # 媒体路径->不透明度(max:80)
        self.plays: Dict[str, bool] = dict() # 媒体路径->是否正在播放
        self.actives: Dict[str, bool] = dict() # 媒体路径->是否处于激活状态
        # 读取配置文件
        self.openConfig()
        # 主界面持有的 wmask组件句柄、wmask窗口句柄
        self.components: Dict[str, WmaskComponent] = dict()
        self.wmasks: Dict[str, Wmask] = dict()
        # 主界面设置
        self.setWindowTitle("Wmask")
        self.setWindowIcon(ICON_FAVICON)
        self.flags = Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowMinimizeButtonHint # 只有最小化
        self.setWindowFlags(self.flags)
        self.setFixedWidth(400)
        self.resize(400, 200)
        ### 》 窗体布局
        # 按钮群
        self.newButton = QPushButton("New", parent=self) # 添加媒体
        self.newButton.clicked.connect(self.newButtonOnClicked)
        self.continueButton = QPushButton("Continue") # 从上次关闭的地方开始
        self.continueButton.clicked.connect(self.continueButtonClicked)
        QTimer.singleShot(10000, lambda : self.continueButton.setDisabled(True)) # 10s后失效
        self.exitButton = QPushButton("Exit", parent=self) # 安全退出
        self.exitButton.clicked.connect(self.exitButtonOnClicked)
        # 按钮群 水平布局
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.newButton)
        self.buttonLayout.addWidget(self.continueButton)
        self.buttonLayout.addWidget(self.exitButton)
        # wmask组件群 垂直布局
        self.componentLayout = QVBoxLayout()
        self.componentLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.componentLayout.setContentsMargins(0, 0, 0, 0)
        # wmask组件群 垂直布局实体组件
        self.componentWidget = QWidget()
        self.componentWidget.setLayout(self.componentLayout)
        # wmask组件群 垂直布局实体组件 垂直滑动区域
        self.componentScroll = QScrollArea(self)
        self.componentScroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.componentScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.componentScroll.setWidgetResizable(True)
        self.componentScroll.setWidget(self.componentWidget)
        # 主界面 垂直布局
        self.centralLayout = QVBoxLayout()
        self.centralLayout.addLayout(self.buttonLayout)
        self.centralLayout.addWidget(self.componentScroll)
        # 主界面 垂直布局实体组件
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.centralLayout)
        self.setCentralWidget(self.centralWidget)
        # 依此逐个载入wmask组件
        for i in self.playlist:
            self.addComponent(i)
        ### 《 窗体布局
        # 同步wmask视频进度到wmask组件进度滑动条
        self.syncPositionTimer = QTimer(self)
        self.syncPositionTimer.setInterval(1000)
        self.syncPositionTimer.timeout.connect(self.syncPositionTimerOnTimeout)
        self.syncPositionTimer.start()
    
    # 读取配置文件
    def openConfig(self, config=DEFAULT_CONFIG):
        if not pathlib.Path(config).is_file():
            return
        with open(config, "r") as fp:
            config_dict = json.load(fp)
        def check(_key:str, _type:type, _default, _dict=config_dict): 
            if _key in _dict and isinstance(_dict[_key], _type):
                return _dict[_key]
            else:
                return _default
        self.folder_path = check("folder_path", str, DEFAULT_FOLDER_PATH)
        self.default_volume = check("default_volume", int, DEFAULT_VOLUME)
        self.default_opacity = check("default_opacity", int, DEFAULT_OPACITY)
        self.default_play = check("default_play", bool, DEFAULT_PLAY)
        self.default_active = check("default_active", bool, DEFAULT_ACTIVE)
        playlist = check("playlist", list, [])
        def addMedia(mediaObj:dict):
            mediaPath = check("mediaPath", str, "", mediaObj)
            if mediaPath == "":
                return
            self.playlist.add(mediaPath)
            self.positions[mediaPath] = check("position", int, 0, mediaObj)
            self.volumes[mediaPath] = check("volume", int, self.default_volume, mediaObj)
            self.opacitys[mediaPath] = check("opacity", int, self.default_opacity, mediaObj)
            self.plays[mediaPath] = check("play", bool, self.default_play, mediaObj)
            self.actives[mediaPath] = check("active", bool, self.default_active, mediaObj)
        for mediaObj in playlist:
            addMedia(mediaObj)
    
    # 保存配置文件
    def saveConfig(self, config=DEFAULT_CONFIG):
        configObj = {}
        configObj["folder_path"] = self.folder_path
        configObj["default_volume"] = self.default_volume
        configObj["default_opacity"] = self.default_opacity
        configObj["default_play"] = self.default_play
        configObj["default_active"] = self.default_active
        configObj["playlist"] = []
        for i in self.playlist:
            mediaObj = {}
            mediaObj["mediaPath"] = i
            mediaObj["position"] = self.components[i].positionSlider.value()
            mediaObj["volume"] = self.components[i].volumeSlider.value()
            mediaObj["opacity"] = self.components[i].opacitySlider.value()
            mediaObj["play"] = self.components[i].playOn
            mediaObj["active"] = self.components[i].activeOn
            configObj["playlist"].append(mediaObj)
        with open(config, "w") as fp:
            json.dump(configObj, fp)
    
    ### 《 按钮群信号槽
    def newButtonOnClicked(self):
        return_lists, _ = QFileDialog.getOpenFileNames(self, "select media", self.folder_path)
        if return_lists:
            self.folder_path = str(pathlib.Path(return_lists[-1]).parent)
        for i in return_lists:
            if i in self.playlist:
                continue
            self.playlist.add(i)
            self.positions[i] = 0
            self.volumes[i] = self.default_volume
            self.opacitys[i] = self.default_opacity
            self.plays[i] = self.default_play
            self.actives[i] = self.default_active
            self.addComponent(i)
    
    def continueButtonClicked(self):
        for i in self.playlist:
            self.components[i].positionSlider.setValue(self.positions[i])
        self.continueButton.setDisabled(True)
    
    def exitButtonOnClicked(self):
        self.saveConfig()
        playlist = self.playlist.copy()
        for i in playlist:
            self.deleteSlot(i)
        self.close()
    ### 《 按钮群信号槽
    
    # 添加wmask组件
    def addComponent(self, mediaPath:str):
        self.components[mediaPath] = WmaskComponent(mediaPath, self.opacitys[mediaPath], self.volumes[mediaPath], self.plays[mediaPath], self.actives[mediaPath], parent=self)
        self.components[mediaPath].playSignal.connect(self.playSlot)
        self.components[mediaPath].activeSignal.connect(self.activeSlot)
        self.components[mediaPath].deleteSignal.connect(self.deleteSlot)
        self.components[mediaPath].positionSignal.connect(self.positionSlot)
        self.components[mediaPath].volumeSignal.connect(self.volumeSlot)
        self.components[mediaPath].opactiySignal.connect(self.opacitySlot)
        if self.actives[mediaPath]:
            self.activeSlot(mediaPath, True)
        self.componentLayout.addWidget(self.components[mediaPath])
    
    ### 》 Wmask组件信号槽
    def playSlot(self, mediaPath:str, play:bool):
        if play:
            self.wmasks[mediaPath].player.play()
        else:
            self.wmasks[mediaPath].player.pause()
    
    def activeSlot(self, mediaPath:str, active:bool):
        if active:
            self.wmasks[mediaPath] = Wmask(mediaPath, self.components[mediaPath].opacitySlider.value(), self.components[mediaPath].volumeSlider.value())
            self.wmasks[mediaPath].player.durationChanged.connect(self.components[mediaPath].positionSlider.setMaximum)
            self.wmasks[mediaPath].player.setPosition(self.components[mediaPath].positionSlider.value())
            self.wmasks[mediaPath].show()
            if self.components[mediaPath].playOn:
                self.wmasks[mediaPath].player.play()
        else:
            self.wmasks[mediaPath].deleteLater()
            del self.wmasks[mediaPath]
    
    def deleteSlot(self, mediaPath:str):
        if self.components[mediaPath].activeOn:
            self.wmasks[mediaPath].deleteLater()
            del self.wmasks[mediaPath]
        self.components[mediaPath].deleteLater()
        del self.components[mediaPath]

        self.playlist.remove(mediaPath)
        self.positions.pop(mediaPath)
        self.opacitys.pop(mediaPath)
        self.volumes.pop(mediaPath)
        self.plays.pop(mediaPath)
        self.actives.pop(mediaPath)
    
    def positionSlot(self, mediaPath:str, position:int):
        if self.components[mediaPath].activeOn:
            self.wmasks[mediaPath].player.setPosition(position)
    
    def volumeSlot(self, mediaPath:str, volume:int):
        if self.components[mediaPath].activeOn:
            self.wmasks[mediaPath].player.setVolume(volume)
    
    def opacitySlot(self, mediaPath:str, opacity:int):
        if self.components[mediaPath].activeOn:
            self.wmasks[mediaPath].setWindowOpacity(opacity / 100)
    ### 《 wmask组件信号槽
    
    # 计时器信号槽
    def syncPositionTimerOnTimeout(self):
        for i in self.playlist:
            if self.components[i].activeOn and self.components[i].playOn:
                self.components[i].positionSlider.blockSignals(True)
                self.components[i].positionSlider.setValue(self.wmasks[i].player.position())
                self.components[i].positionSlider.blockSignals(False)


# wmask组件
class WmaskComponent(QWidget):
    # 信号
    playSignal = pyqtSignal(str, bool)
    activeSignal = pyqtSignal(str, bool)
    deleteSignal = pyqtSignal(str)
    positionSignal = pyqtSignal(str, int)
    volumeSignal = pyqtSignal(str, int)
    opactiySignal = pyqtSignal(str, int)

    def __init__(self, mediaPath:str, opacity:int, volume:int, play:bool, active:bool, parent):
        super().__init__(parent)
        self.mediaPath = mediaPath
        # 名称标签
        self.nameLabel = QLabel(pathlib.Path(mediaPath).name, parent=self)
        # 播放/暂停键
        self.playOn = play
        self.playButton = QPushButton(parent=self)
        self.playButton.setFixedWidth(30)
        self.playButton.setIcon(ICON_MEDIA_PLAYBACK_PAUSE if play else ICON_MEDIA_PLAYBACK_START)
        self.playButton.clicked.connect(self.playButtonOnClicked)
        # 激活/关闭键
        self.activeOn = active
        self.activeButton = QPushButton(parent=self)
        self.activeButton.setFixedWidth(30)
        self.activeButton.setIcon(ICON_SYSTEM_SHUTDOWN if active else ICON_SYSTEM_RUN)
        self.activeButton.clicked.connect(self.activeButtonOnClicked)
        # 删除键
        self.deleteButton = QPushButton(parent=self)
        self.deleteButton.setFixedWidth(30)
        self.deleteButton.setIcon(ICON_WINDOW_CLOSE)
        self.deleteButton.clicked.connect(self.deleteButtonOnClicked)
        # 上面四个组件 水平布局
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.nameLabel)
        self.hlayout.addWidget(self.playButton)
        self.hlayout.addWidget(self.activeButton)
        self.hlayout.addWidget(self.deleteButton)
        # 进度
        self.positionLabel = QLabel("progress", parent=self)
        self.positionLabel.setFixedWidth(80)
        self.positionSlider = QSlider(Qt.Orientation.Horizontal, parent=self)
        self.positionSlider.setMinimum(0)
        self.positionSlider.setSingleStep(1000)
        self.positionSlider.valueChanged.connect(lambda x: self.positionSignal.emit(self.mediaPath, x))
        # 进度 水平布局
        self.h1layout = QHBoxLayout()
        self.h1layout.addWidget(self.positionLabel)
        self.h1layout.addWidget(self.positionSlider)
        # 音量
        self.volumeLabel = QLabel("volume", parent=self)
        self.volumeLabel.setFixedWidth(80)
        self.volumeSlider = QSlider(Qt.Orientation.Horizontal, parent=self)
        self.volumeSlider.setMinimum(0)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setSingleStep(1)
        self.volumeSlider.setValue(volume)
        self.volumeSlider.valueChanged.connect(lambda x: self.volumeSignal.emit(self.mediaPath, x))
        # 音量 水平布局
        self.h2layout = QHBoxLayout()
        self.h2layout.addWidget(self.volumeLabel)
        self.h2layout.addWidget(self.volumeSlider)
        # 不透明度
        self.opacityLabel = QLabel("opacity", parent=self)
        self.opacityLabel.setFixedWidth(80)
        self.opacitySlider = QSlider(Qt.Orientation.Horizontal, parent=self)
        self.opacitySlider.setMinimum(0)
        self.opacitySlider.setMaximum(80)
        self.opacitySlider.setSingleStep(1)
        self.opacitySlider.setValue(opacity)
        self.opacitySlider.valueChanged.connect(lambda x: self.opactiySignal.emit(self.mediaPath, x))
        # 不透明度 水平布局
        self.h3layout = QHBoxLayout()
        self.h3layout.addWidget(self.opacityLabel)
        self.h3layout.addWidget(self.opacitySlider)
        # 总 垂直布局
        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(self.hlayout)
        self.vlayout.addLayout(self.h1layout)
        self.vlayout.addLayout(self.h2layout)
        self.vlayout.addLayout(self.h3layout)
        self.setLayout(self.vlayout)
        # 窗体尺寸
        self.setFixedHeight(120)
        self.setFixedWidth(parent.width()-40)
    
    ### 《 转发信号
    def playButtonOnClicked(self):
        if not self.activeOn:
            return
        self.playButton.setIcon(ICON_MEDIA_PLAYBACK_START if self.playOn else ICON_MEDIA_PLAYBACK_PAUSE)
        self.playOn ^= True
        self.playSignal.emit(self.mediaPath, self.playOn)
    
    def activeButtonOnClicked(self):
        self.activeButton.setIcon(ICON_SYSTEM_RUN if self.activeOn else ICON_SYSTEM_SHUTDOWN)
        self.activeOn ^= True
        self.activeSignal.emit(self.mediaPath, self.activeOn)
    
    def deleteButtonOnClicked(self):
        self.deleteSignal.emit(self.mediaPath)
    ### 》 转发信号


# wmask窗体
class Wmask(QWidget):
    def __init__(self, mediaPath:str, opacity:int, volume:int):
        super().__init__()
        self.mediaPath = mediaPath
        # 设置全屏
        desktop = QApplication.desktop()
        screen_size = desktop.screenGeometry(desktop.screenNumber(self))
        self.resize(screen_size.width(), screen_size.height())
        # 窗体属性
        self.setWindowOpacity(opacity / 100) # 不透明度
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True) # 鼠标事件穿透
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent) # 视频循环播放时，播完到重新开始不重绘，以防止闪屏
        self.flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.BypassWindowManagerHint | Qt.WindowType.WindowStaysOnTopHint # 无边框 | 键盘鼠标事件穿透 | 置顶窗体
        self.setWindowFlags(self.flags)
        # 视频输出组件
        self.video_widget = QVideoWidget(parent=self)
        self.video_widget.resize(self.width(), self.height())
        # 播放列表（其实只有单一视频，但为了循环播放，需要设置一个播放列表）
        self.playlist = QMediaPlaylist(parent=self)
        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(self.mediaPath)))
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        # 播放器
        self.player = QMediaPlayer(parent=self)
        self.player.setPlaylist(self.playlist)
        self.player.setVideoOutput(self.video_widget)
        self.player.setVolume(volume)


# base64字符串转QIcon
def base64ToQIcon(_base64:bytes):
    qpixmap = QPixmap()
    qpixmap.loadFromData(QByteArray.fromBase64(_base64))
    return QIcon(qpixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # favicon
    ICON_FAVICON = base64ToQIcon(b"iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAAAAAAAAQCEeRdzAAACKklEQVR4nO2ZvUoDQRDHJzZqSh/AwhiNirWf2PoMVtr7GgE1aPQFLPyGdFa+gIUPYGXjJyRgDIIiaDQ6w87hJrlNNuvt3UbuDz849obN7Gbmn2UDECtWrFj/UQNIFikzWR4LKt66KIEq8s1UeSyoeOsqS8l4lAOMt66uX0DXl9AkUkE+mAqP6cQ70cQbyB0yjKT4OdciPscxKfuptVcGxC5uI31MnscyLeLzHBupEsghUkJmpXF6LvK7hE98sSE+Ms2ASOYI6ZHGVYmqFhaJvFJ5QsZ83jeWSrvSCl3UgLfIJqh3U25WneYOVeQ89yCcRyU5aaedRyW5bJxyngMQzjOnEe81rjPOMw0imWOodx6VnFoAff1bIJxnXDPeqRLynIcWoePjzjXxOrR3HllO2ego8ojsgF4ZOPVDRuWyD/rO49xRwtR5nDjM0VdPxwUT53HiOD2E3ICZ86gUqiOtIQ9g5jwqheZII/DrPP0a8brlEYojUbnsgXCeec34ThrUuiNN8QecwN+cRyWrjiQ7z4RmvElJWHMkcp5rnjgo51EpMEeiJl0FcVj7Ql5AlJFK8g2zzmWWSt4R5QLZRRaRXoN5YAlE0t51Xw05BXX9B3U9uII8S/NQ2S4bzANn0Hzh+gnCSv3kd0H7ilx2SMVnnqtuWsC7zzxvJguIqoQK0LyAgsE8dU1MO0kNNdgiPqi/idLIOYgNq/Fz2mCeSJVEFphkxLnEihXLpn4AChIW6yQNMxgAAAAASUVORK5CYII=")
    # 媒体播放键
    ICON_MEDIA_PLAYBACK_START = base64ToQIcon(b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAN1wAADdcBQiibeAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAATdEVYdFRpdGxlAE9wdGljYWwgRHJpdmU+Z7oMAAABg0lEQVQ4jcWTS0tCURDH5+jJezNNLKpv0AOKHlK0CVwFtesjRAs3PWgTtHKhmwiCFi1amASCLSRLK2+ZFhmtSoWgWhdooPgI70O795x2YaZluGhgFgPz//GfYQZRSqGRUDWkBgBcXoQuT28pAQ6rGLvZbJb+7IAQYurp7l0BtfwcDHMzdVmglH7mWeiEyrJMRVGgD0/30vkFdxMMHvWV91TmFweSJIGiyJDJpqGzo4sxDY+Ns1pd7Jg73AoEAq2/jsDzPBBCQCyK8JpKQjqbQgP9g8zI0KhFpqUXt8c1CwDoR4BCFJCKEmCMAavVIIg86PV69dTkdGuTCu84drcnyjW4EkAIAYwxMBoGmlkt6Fr0kM/nlf2wR8hlc0uL88uRmgCBFwAhBCzDgtHQBrJMqM/vLSUSSUcBi6vWBetb5Q6+OWA0LBgN7XAduSpG49FoURTmbLa1x2oLrAqIxaPvPv9BThAFy8b6preWsCpAhdCde8/F5TIFu9PprOsS0b8/U8OAD1i6yfAlA768AAAAAElFTkSuQmCC")
    # 媒体暂停键
    ICON_MEDIA_PLAYBACK_PAUSE = base64ToQIcon(b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAN1wAADdcBQiibeAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAATdEVYdFRpdGxlAE9wdGljYWwgRHJpdmU+Z7oMAAAA7ElEQVQ4jdWTwUoDMRRFz3sTZvoH6beIKIOFfpsLcSfoj4hYqFj8FWlcqMvJTJO4GA2t2lEYN75N8g7kcO8iklJizOio138hMNvLYnmzTilaABV1J/V8ulher1PCAoiom9Xz6V5BStHWRzNAWN7f2p5hDw+OERFWD3d2sELXdQC4p8d870/h5fU5s70C7z0hRpq2wXufmYhQlVVmA4KWEDY0vsH7NjMVoSyrzIYThIAxZieBqlJVk28TmM8CYCduLyhQ1d9U+Og7+ZIgxvhzgrDp3OXVhQUoCuMAYgju7PzUAph3tj3y///CaMEbabKLq8akpOcAAAAASUVORK5CYII=")
    # 媒体激活建
    ICON_SYSTEM_RUN = base64ToQIcon(b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAA3NCSVQICAjb4U/gAAAACXBIWXMAAA3XAAAN1wFCKJt4AAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAABN0RVh0VGl0bGUAT3B0aWNhbCBEcml2ZT5nugwAAABgUExURf///wAAAP///4CAgFhbV1hbVp+gnXN0ca6uq3N1ca2trK+wrcfIxlVXU0JDQVVXU1VXU1ZYVGxuaoiKhcXFxM/PzuHh4OLi4O7u7PHx8fLz8vf39/j4+Pv7+/z8+/7+/mcCE4sAAAAQdFJOUwABAQKzt/b6+vv7+/z9/v7YPlFDAAAAdUlEQVQYlXWOWQ6AIAwFAfeVQl1QVO5/SxsTAUN8f22mb8qYDyKyOJk2OotmMe5uH0Xg9dZW7ab9FRrXiMYZ/CU+HY9PAVlAeR/MK+3XGV5WLsdlr2ORoe0sh/Ksi+CzwMFOPCWSDtqQRZCl67vH4v/IeQ6K3yejC9e2pE6uAAAAAElFTkSuQmCC")
    # 媒体失活键
    ICON_SYSTEM_SHUTDOWN = base64ToQIcon(b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAA3NCSVQICAjb4U/gAAAACXBIWXMAAA3XAAAN1wFCKJt4AAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAANhQTFRFnZ2dnp6eoKCgn5+fnZ2dnJyc0NDQ09PTAAAABQUFDxAPJicmQ0RBX2BdYGFgaGhodHR0e314iIqFiYmJjpCLj5GMm5ubsbKwsrKys7Ozu7u7vL+4vb68wMDAxMTExcfCxsjDyMjIzMzMz8/P0dHR1dXV1tbW19fX2NjY2dnZ3d3d3t7e39/f4ODg4eHh4+Pj5OTk5eXl5ubm5+fn6Ojo6enp6urq6+vr7Ozs7e3t7u7u7+/v8PDw8fHx8vLy8/Pz9PT09vb2+vr6+/v7/Pz8/f39/v7+////R6AftQAAAAh0Uk5TGqamp/n6/f1ShpYZAAAAqUlEQVQYV12Pu41CQRAEu3dm3xNIGDznQjiPECB3QsDHIQAQAsQdOx+MBQzaLJVKakLKEu+dwpWylg/wbYhuzjYCQKZf7r8HnaRNj+zC7CSTAiVt90hwWLEAChSLVguiRXbAdFZA3IPd8GAl8j+sdqM5fwDc3IZutNARgIa9GhZcKIyRvUFP2TeouHUA43gNFLEEoMeQ+WU+/AmlLSSOLHVd3t8Q28bv+09M609MRKtpUAAAAABJRU5ErkJggg==")
    # wmask组件删除键
    ICON_WINDOW_CLOSE = base64ToQIcon(b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAA3NCSVQICAjb4U/gAAAACXBIWXMAAA3XAAAN1wFCKJt4AAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAALpQTFRF////YWRfYGNgX19dX2FdYWFdXmBcYGNcYGReYmRgYWNfYGJeYGJcYGJeYmReYmRgYWNdYmRgYGJeYGReYmReYWNfX2FdYGJeYWJfY2VgYmRgY2ZhYmReY2ZhZGZhYGRffH55enx2en13e313fH55f4F8gIJ9gIJ+g4WAhIaBio2Gi42IfH55fYB6gYN9gYR9g4WAhYeChomDio2IsLOrsbSsuby0ur21ur62wMS8wcS8wsa+w8a+x8vDi9cj2gAAADR0Uk5TAG5vdnZ2d3d4eHl6fX19fX5/gICAhIaSmdnd3eDh4uTs7e3t7e3t7e3t7e3u7u7u7u7u7ttMubAAAABxSURBVBiVY2AgC4jJc4IoZnlRqICUqa4QAwOPkokkVIBF11xPiEfJVIURpkfAwNJIzVSHA2GKoLGVmT4XkrH82jYWquwIPp+mrZaGqSJchFXd2lCEV9lUkQkqIGemIQy0VsFUBiogIcsNotikxcnzGAAVDQmLdEUqbgAAAABJRU5ErkJggg==")
    wmask_main = WmaskMain()
    wmask_main.show()
    sys.exit(app.exec_())
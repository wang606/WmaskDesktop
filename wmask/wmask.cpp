#include "wmask.h"
#include <QApplication>
#include <QGuiApplication>
#include <QUrl>

Wmask::Wmask(QString mediaPath, int volume, int opacity, QWidget *parent)
    : QWidget{parent}
{
    this->mediaPath = mediaPath;
    // fullscreen
    QDesktopWidget* desktop = QApplication::desktop();
    QRect screen_size = QGuiApplication::screens().at(desktop->screenNumber(this))->geometry();
    this->resize(screen_size.width(), screen_size.height());
    // window attribute
    this->setWindowOpacity((double)opacity / 100);
    this->setAttribute(Qt::WidgetAttribute::WA_TransparentForMouseEvents);
    this->setAttribute(Qt::WidgetAttribute::WA_OpaquePaintEvent);
    QFlags<Qt::WindowType> flags = Qt::WindowType::FramelessWindowHint | Qt::WindowType::BypassWindowManagerHint | Qt::WindowType::WindowStaysOnTopHint;
    this->setWindowFlags(flags);
    // video_widget
    this->video_widget = new QVideoWidget(this);
    this->video_widget->resize(this->width(), this->height());
    // playlist (just for loop)
    this->playlist = new QMediaPlaylist(this);
    this->playlist->addMedia(QMediaContent(QUrl::fromLocalFile(QFileInfo(this->mediaPath).absoluteFilePath())));
    this->playlist->setPlaybackMode(QMediaPlaylist::Loop);
    // player
    this->player = new QMediaPlayer(this);
    this->player->setPlaylist(this->playlist);
    this->player->setVideoOutput(this->video_widget);
    this->player->setVolume(volume);
}

void Wmask::closeEvent(QCloseEvent *event) {
    event->setAccepted(true);
    emit this->wmaskCloseSignal(this->mediaPath);
}

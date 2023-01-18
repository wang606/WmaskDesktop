#ifndef WMASK_H
#define WMASK_H

#include <QWidget>
#include <QVideoWidget>
#include <QMultimedia>
#include <QtMultimediaWidgets>
#include <QCloseEvent>

class Wmask : public QWidget
{
    Q_OBJECT
public:
    explicit Wmask(QString mediaPath, int volume, int opacity, QWidget *parent = nullptr);
    QString mediaPath;
    QVideoWidget* video_widget;
    QMediaPlayer* player;
    QMediaPlaylist* playlist;
private:
    void closeEvent(QCloseEvent *event);
signals:
    void wmaskCloseSignal(QString mediaPath);
};

#endif // WMASK_H

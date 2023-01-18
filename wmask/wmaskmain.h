#ifndef WMASKMAIN_H
#define WMASKMAIN_H

#include "wmaskcomponent.h"
#include "wmask.h"
#include <QMainWindow>
#include <QDir>
#include <QSet>
#include <QMap>
#include <QPushButton>
#include <QTimer>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QScrollArea>
#include <QCloseEvent>

const QString DEFAULT_CONFIG = QDir::home().filePath(".wmask");
const QString DEFAULT_FOLDER_PATH = QDir::currentPath();
const int DEFAULT_VOLUME = 30;
const int DEFAULT_OPACITY = 20;
const bool DEFAULT_PLAY = false;
const bool DEFAULT_ACTIVE = false;

class WmaskMain : public QMainWindow
{
    Q_OBJECT

public:
    WmaskMain(QWidget *parent = nullptr);
    ~WmaskMain();
    QString folder_path;
    int default_volume;
    int default_opacity;
    bool default_play;
    bool default_active;
    QSet<QString> playlist;
    QMap<QString, int> positions;
    QMap<QString, int> volumes;
    QMap<QString, int> opacitys;
    QMap<QString, bool> plays;
    QMap<QString, bool> actives;
    QMap<QString, WmaskComponent*> components;
    QMap<QString, Wmask*> wmasks;

    QPushButton *newButton;
    QHBoxLayout *buttonLayout;
    QVBoxLayout *componentLayout, *central_layout;
    QScrollArea *componentScroll;
    QWidget *componentWidget, *central_widget;
    QTimer *syncPositionTimer;
private:
    void closeEvent(QCloseEvent *event);
public slots:
    void openConfig(QString config=DEFAULT_CONFIG);
    void saveConfig(QString config=DEFAULT_CONFIG);
    void newButtonOnClicked();
    void addComponent(QString mediaPath);
    void playSlot(QString mediaPath, bool play);
    void activeSlot(QString mediaPath, bool active);
    void deleteSlot(QString mediaPath);
    void positionSlot(QString mediaPath, int position);
    void volumeSlot(QString mediaPath, int volume);
    void opacitySlot(QString mediaPath, int opacity);
    void wmaskCloseSlot(QString mediaPath);
    void syncPositionTimerOnTimeout();
};
#endif // WMASKMAIN_H

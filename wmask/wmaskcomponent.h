#ifndef WMASKCOMPONENT_H
#define WMASKCOMPONENT_H

#include <QWidget>
#include <QLabel>
#include <QPushButton>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QSlider>
#include <QComboBox>

class WmaskComponent : public QWidget
{
    Q_OBJECT
public:
    explicit WmaskComponent(QString mediaPath, int position, int volume, int opacity, bool play, bool active, QWidget *parent = nullptr);
    QString mediaPath;
    bool playOn, activeOn;
    QLabel *nameLabel, *positionLabel, *volumeLabel, *opacityLabel;
    QPushButton *playButton, *activeButton, *deleteButton;
    QSlider *positionSlider, *volumeSlider, *opacitySlider;
    QHBoxLayout *hlayout, *h1layout, *h2layout, *h3layout;
    QVBoxLayout *vlayout;
public slots:
    void playButtonOnClicked();
    void activeButtonOnClicked();
    void deleteButtonOnClicked();
signals:
    void playSignal(QString, bool);
    void activeSignal(QString, bool);
    void deleteSignal(QString);
    void positionSignal(QString, int);
    void volumeSignal(QString, int);
    void opacitySignal(QString, int);
};

#endif // WMASKCOMPONENT_H

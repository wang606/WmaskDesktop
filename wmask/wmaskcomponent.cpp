#include "wmaskcomponent.h"
#include "wmaskicons.h"
#include <QDir>
#include <QSizePolicy>

WmaskComponent::WmaskComponent(QString mediaPath, int position, int volume, int opacity, bool play, bool active, QWidget *parent)
    : QWidget{parent}
{
    this->mediaPath = mediaPath;
    // nameLabel
    this->nameLabel = new QLabel(QDir(this->mediaPath).dirName(), this);
    this->nameLabel->setToolTip(this->mediaPath);
    // play/pause
    this->playOn = play;
    this->playButton = new QPushButton(this);
    this->playButton->setEnabled(active);
    this->playButton->setFixedWidth(30);
    this->playButton->setIcon(play ? ICON_MEDIA_PLAYBACK_PAUSE() : ICON_MEDIA_PLAYBACK_START());
    connect(this->playButton, &QPushButton::clicked, this, &WmaskComponent::playButtonOnClicked);
    // active/deactive
    this->activeOn = active;
    this->activeButton = new QPushButton(this);
    this->activeButton->setFixedWidth(30);
    this->activeButton->setIcon(active ? ICON_SYSTEM_SHUTDOWN() : ICON_SYSTEM_RUN());
    connect(this->activeButton, &QPushButton::clicked, this, &WmaskComponent::activeButtonOnClicked);
    // delete
    this->deleteButton = new QPushButton(this);
    this->deleteButton->setFixedWidth(30);
    this->deleteButton->setIcon(ICON_WINDOW_CLOSE());
    connect(this->deleteButton, &QPushButton::clicked, this, &WmaskComponent::deleteButtonOnClicked);
    // hlayout
    this->hlayout = new QHBoxLayout();
    this->hlayout->addWidget(this->nameLabel);
    this->hlayout->addWidget(this->playButton);
    this->hlayout->addWidget(this->activeButton);
    this->hlayout->addWidget(this->deleteButton);
    // progress
    this->positionLabel = new QLabel("progress", this);
    this->positionLabel->setFixedWidth(50);
    this->positionSlider = new QSlider(Qt::Orientation::Horizontal, this);
    this->positionSlider->setFixedHeight(20);
    this->positionSlider->setMinimum(0);
    this->positionSlider->setMaximum(2 * position);
    this->positionSlider->setSingleStep(1000);
    this->positionSlider->setValue(position);
    connect(this->positionSlider, &QSlider::valueChanged, this, [this](int x){emit this->positionSignal(this->mediaPath, x); });
    // progress h1layout
    this->h1layout = new QHBoxLayout();
    this->h1layout->addWidget(this->positionLabel);
    this->h1layout->addWidget(this->positionSlider);
    // volume
    this->volumeLabel = new QLabel("volume", this);
    this->volumeLabel->setFixedWidth(50);
    this->volumeSlider = new QSlider(Qt::Orientation::Horizontal, this);
    this->volumeSlider->setFixedHeight(20);
    this->volumeSlider->setMinimum(0);
    this->volumeSlider->setMaximum(100);
    this->volumeSlider->setSingleStep(1);
    this->volumeSlider->setValue(volume);
    connect(this->volumeSlider, &QSlider::valueChanged, this, [this](int x){emit this->volumeSignal(this->mediaPath, x); });
    // volume h2layout
    this->h2layout = new QHBoxLayout();
    this->h2layout->addWidget(this->volumeLabel);
    this->h2layout->addWidget(this->volumeSlider);
    // opacity
    this->opacityLabel = new QLabel("opacity", this);
    this->opacityLabel->setFixedWidth(50);
    this->opacitySlider = new QSlider(Qt::Orientation::Horizontal, this);
    this->opacitySlider->setFixedHeight(20);
    this->opacitySlider->setMinimum(0);
    this->opacitySlider->setMaximum(80);
    this->opacitySlider->setSingleStep(1);
    this->opacitySlider->setValue(opacity);
    connect(this->opacitySlider, &QSlider::valueChanged, this, [this](int x){emit this->opacitySignal(this->mediaPath, x); });
    // opacity h3layout
    this->h3layout = new QHBoxLayout();
    this->h3layout->addWidget(this->opacityLabel);
    this->h3layout->addWidget(this->opacitySlider);
    // vlayout
    this->vlayout = new QVBoxLayout();
    this->vlayout->setContentsMargins(0, 0, 15, 0);
    this->vlayout->addLayout(this->hlayout);
    this->vlayout->addLayout(this->h1layout);
    this->vlayout->addLayout(this->h2layout);
    this->vlayout->addLayout(this->h3layout);
    this->setLayout(this->vlayout);
    // widget size
    this->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Minimum);
//    this->setFixedHeight(120);
    this->setFixedWidth(parent->width() - 40);
}

void WmaskComponent::playButtonOnClicked() {
    if (!this->activeOn) {
        return;
    }
    this->playOn ^= true;
    this->playButton->setIcon(this->playOn ? ICON_MEDIA_PLAYBACK_PAUSE() : ICON_MEDIA_PLAYBACK_START());
    emit this->playSignal(this->mediaPath, this->playOn);
}

void WmaskComponent::activeButtonOnClicked() {
    this->activeOn ^= true;
    this->playButton->setEnabled(this->activeOn);
    this->activeButton->setIcon(this->activeOn ? ICON_SYSTEM_SHUTDOWN() : ICON_SYSTEM_RUN());
    emit this->activeSignal(this->mediaPath, this->activeOn);
}

void WmaskComponent::deleteButtonOnClicked() {
    emit this->deleteSignal(this->mediaPath);
}

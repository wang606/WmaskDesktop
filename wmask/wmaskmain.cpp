#include "wmaskmain.h"
#include "wmaskicons.h"
#include <fstream>
#include "json.hpp"
using json = nlohmann::json;
#ifdef QT_DEBUG
#include <QtDebug>
#endif

WmaskMain::WmaskMain(QWidget *parent)
    : QMainWindow(parent)
{
    this->folder_path = DEFAULT_FOLDER_PATH;
    this->default_volume = DEFAULT_VOLUME;
    this->default_opacity = DEFAULT_OPACITY;
    this->default_play = DEFAULT_PLAY;
    this->default_active = DEFAULT_ACTIVE;
    this->openConfig();
    // main window setting
    this->setWindowTitle("Wmask");
    this->setWindowIcon(ICON_FAVICON());
    this->setFixedWidth(400);
    this->resize(400, 200);
    // window layout
    // buttons
    this->newButton = new QPushButton("New", this);
    connect(this->newButton, &QPushButton::clicked, this, &WmaskMain::newButtonOnClicked);
    // buttonLayout
    this->buttonLayout = new QHBoxLayout();
    this->buttonLayout->addWidget(this->newButton);
    // componentLayout
    this->componentLayout = new QVBoxLayout();
    this->componentLayout->setAlignment(Qt::AlignmentFlag::AlignTop);
    // componentWidget
    this->componentWidget = new QWidget();
    this->componentWidget->setLayout(this->componentLayout);
    // componentScroll
    this->componentScroll = new QScrollArea(this);
    this->componentScroll->setVerticalScrollBarPolicy(Qt::ScrollBarPolicy::ScrollBarAlwaysOn);
    this->componentScroll->setHorizontalScrollBarPolicy(Qt::ScrollBarPolicy::ScrollBarAlwaysOff);
    this->componentScroll->setWidgetResizable(true);
    this->componentScroll->setWidget(this->componentWidget);
    // central_layout
    this->central_layout = new QVBoxLayout();
    this->central_layout->addLayout(this->buttonLayout);
    this->central_layout->addWidget(this->componentScroll);
    // central_widget
    this->central_widget = new QWidget();
    this->central_widget->setLayout(this->central_layout);
    this->setCentralWidget(this->central_widget);
    // load wmaskcomponents
    for (QString i : this->playlist) {
        this->addComponent(i);
    }
    // syncPositionTimer
    this->syncPositionTimer = new QTimer(this);
    this->syncPositionTimer->setInterval(1000);
    connect(this->syncPositionTimer, &QTimer::timeout, this, &WmaskMain::syncPositionTimerOnTimeout);
    this->syncPositionTimer->start();
}

WmaskMain::~WmaskMain()
{
}

void WmaskMain::closeEvent(QCloseEvent *event) {
    this->saveConfig();
    QList<QString> playlist = this->playlist.values();
    for (QString i: playlist) {
        this->deleteSlot(i);
    }
    event->setAccepted(true);
}

void WmaskMain::openConfig(QString config) {
    try {
        std::ifstream config_file(config.toStdString());
        json config_json = json::parse(config_file);
        this->folder_path = QString::fromStdString(config_json["folder_path"]);
        this->default_volume = config_json["default_volume"];
        this->default_opacity = config_json["default_opacity"];
        this->default_play = config_json["default_play"];
        this->default_active = config_json["default_active"];
        for (auto i: config_json["playlist"]) {
            std::string _str = i["mediaPath"];
            QString mediaPath(_str.c_str());
            this->playlist.insert(mediaPath);
            this->positions.insert(mediaPath, i["position"]);
            this->volumes.insert(mediaPath, i["volume"]);
            this->opacitys.insert(mediaPath, i["opacity"]);
            this->plays.insert(mediaPath, i["play"]);
            this->actives.insert(mediaPath, i["active"]);
        }
    } catch (...) {}
    return;
}

void WmaskMain::saveConfig(QString config) {
    json config_json;
    config_json["folder_path"] = this->folder_path.toStdString();
    config_json["default_volume"] = this->default_volume;
    config_json["default_opacity"] = this->default_opacity;
    config_json["default_play"] = this->default_play;
    config_json["default_active"] = this->default_active;
    config_json["playlist"] = json::array();
    for (QString i: this->playlist) {
        config_json["playlist"].push_back({
            {"mediaPath", i.toStdString()},
            {"position", this->components[i]->positionSlider->value()},
            {"volume", this->components[i]->volumeSlider->value()},
            {"opacity", this->components[i]->opacitySlider->value()},
            {"play", this->components[i]->playOn},
            {"active", this->components[i]->activeOn}
        });
    }
    std::ofstream config_file(config.toStdString());
    config_file << config_json;
    return;
}

void WmaskMain::newButtonOnClicked() {
    QStringList return_list = QFileDialog::getOpenFileNames(this, "select media", this->folder_path, "Media Files (*.mp4 *.MP4 *.avi *.AVI *.mkv *.MKV *.webm *.WebM *.mov *.MOV *.flv *.FLV *.ogg *.OGG);;All Files (*.*)");
    if (!return_list.empty()) {
        this->folder_path = QFileInfo(return_list.last()).dir().absolutePath();
    }
    for (QString i: return_list) {
        if (this->playlist.contains(i)) {
            continue;
        }
        this->playlist.insert(i);
        this->positions.insert(i, 0);
        this->volumes.insert(i, this->default_volume);
        this->opacitys.insert(i, this->default_opacity);
        this->plays.insert(i, this->default_play);
        this->actives.insert(i, this->default_active);
        this->addComponent(i);
    }
}

void WmaskMain::addComponent(QString mediaPath) {
    this->components.insert(mediaPath, new WmaskComponent(mediaPath, this->positions[mediaPath], this->volumes[mediaPath], this->opacitys[mediaPath], this->plays[mediaPath], this->actives[mediaPath], this));
    connect(this->components[mediaPath], &WmaskComponent::playSignal, this, &WmaskMain::playSlot);
    connect(this->components[mediaPath], &WmaskComponent::activeSignal, this, &WmaskMain::activeSlot);
    connect(this->components[mediaPath], &WmaskComponent::deleteSignal, this, &WmaskMain::deleteSlot);
    connect(this->components[mediaPath], &WmaskComponent::positionSignal, this, &WmaskMain::positionSlot);
    connect(this->components[mediaPath], &WmaskComponent::volumeSignal, this, &WmaskMain::volumeSlot);
    connect(this->components[mediaPath], &WmaskComponent::opacitySignal, this, &WmaskMain::opacitySlot);
    if (this->actives[mediaPath]) {
        this->activeSlot(mediaPath, true);
    }
    this->componentLayout->addWidget(this->components[mediaPath]);
}

void WmaskMain::playSlot(QString mediaPath, bool play) {
    if (!this->components[mediaPath]->activeOn) {
        return;
    }
    if (play) {
        this->wmasks[mediaPath]->player->play();
    } else {
        this->wmasks[mediaPath]->player->pause();
    }
}

void WmaskMain::activeSlot(QString mediaPath, bool active) {
    if (active) {
        this->wmasks.insert(mediaPath, new Wmask(mediaPath, this->components[mediaPath]->volumeSlider->value(), this->components[mediaPath]->opacitySlider->value()));
        connect(this->wmasks[mediaPath]->player, &QMediaPlayer::durationChanged, this->components[mediaPath]->positionSlider, [this, mediaPath](int x) { if (x > 0) this->components[mediaPath]->positionSlider->setMaximum(x); });
        connect(this->wmasks[mediaPath], &Wmask::wmaskCloseSignal, this, &WmaskMain::wmaskCloseSlot);
        this->wmasks[mediaPath]->player->setPosition(this->components[mediaPath]->positionSlider->value());
        this->wmasks[mediaPath]->show();
        if (this->components[mediaPath]->playOn) {
            this->wmasks[mediaPath]->player->play();
        }
    } else {
        this->wmasks[mediaPath]->deleteLater();
        this->wmasks.remove(mediaPath);
    }
}

void WmaskMain::deleteSlot(QString mediaPath) {
    this->playlist.remove(mediaPath);

    if (this->components[mediaPath]->activeOn) {
        this->components[mediaPath]->activeButton->clicked();
    }
    this->componentLayout->removeWidget(this->components[mediaPath]);
    this->components[mediaPath]->close();
    this->components[mediaPath]->deleteLater();
    this->components.remove(mediaPath);

    this->positions.remove(mediaPath);
    this->volumes.remove(mediaPath);
    this->opacitys.remove(mediaPath);
    this->plays.remove(mediaPath);
    this->actives.remove(mediaPath);
}

void WmaskMain::positionSlot(QString mediaPath, int position) {
    if (this->components.contains(mediaPath) && this->components[mediaPath]->activeOn) {
        this->wmasks[mediaPath]->player->setPosition(position);
    }
}

void WmaskMain::volumeSlot(QString mediaPath, int volume) {
    if (this->components.contains(mediaPath) && this->components[mediaPath]->activeOn) {
        this->wmasks[mediaPath]->player->setVolume(volume);
    }
}

void WmaskMain::opacitySlot(QString mediaPath, int opacity) {
    if (this->components.contains(mediaPath) && this->components[mediaPath]->activeOn) {
        this->wmasks[mediaPath]->setWindowOpacity((double)opacity / 100);
    }
}

void WmaskMain::wmaskCloseSlot(QString mediaPath) {
    if (this->components[mediaPath]->activeOn) {
        // except close
        this->components[mediaPath]->activeButton->clicked();
    }
}

void WmaskMain::syncPositionTimerOnTimeout() {
    for (QString i: this->playlist) {
        if (this->components[i]->activeOn && this->components[i]->playOn) {
            this->components[i]->positionSlider->blockSignals(true);
            this->components[i]->positionSlider->setValue(this->wmasks[i]->player->position());
            this->components[i]->positionSlider->blockSignals(false);
        }
    }
}


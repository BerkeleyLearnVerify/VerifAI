#include "OSMImportWidget.hpp"

OSMImportWidget::OSMImportWidget(QWidget *parent):
  QWidget(parent)
{
  mLayout = new QVBoxLayout(this);
  mPushButton = new QPushButton("Start OpenStreetMap importer graphical user interface", this);
  mLayout->addWidget(mPushButton);
  connect(mPushButton, &QPushButton::pressed, this, &OSMImportWidget::launchExecutable);
}

OSMImportWidget::~OSMImportWidget() {
}

void OSMImportWidget::launchExecutable() {
  QString gui_executable = qgetenv("WEBOTS_HOME") + QString("/resources/osm_importer/osm_gui/osm_gui"); // TODO, need to handle Windows
  const QStringList arguments = QStringList(qgetenv("WEBOTS_HOME") + QString("/resources/osm_importer/importer.py"));
  QProcess::startDetached(gui_executable, arguments);
}

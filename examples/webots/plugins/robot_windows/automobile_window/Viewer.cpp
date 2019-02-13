#include "GeneralInformationWidget.hpp"
#include "SpeedWidget.hpp"
#include "SteeringWidget.hpp"
#include "EncodersWidget.hpp"
#include "BrakeWidget.hpp"
#include "ThrottleWidget.hpp"
#include "RPMWidget.hpp"
#include "OSMImportWidget.hpp"
#include "Viewer.hpp"

using namespace webotsQtUtils;

QStringList hiddenDevices = (QStringList() << "left_steer" << "right_steer" << "right_steer_sensor" << "left_steer_sensor"
                            << "left_front_wheel" << "right_front_wheel" << "left_rear_wheel" << "right_rear_wheel"
                            << "left_front_sensor" << "right_front_sensor" << "left_rear_sensor" << "right_rear_sensor"
                            << "left_wiper_motor" << "right_wiper_motor" << "wiper_sensor" << "left_wing_yaw_mirror_motor"
                            << "left_wing_pitch_mirror_motor" << "right_wing_yaw_mirror_motor" << "right_wing_pitch_mirror_motor"
                            << "rear_yaw_mirror_motor" << "rear_pitch_mirror_motor");

Viewer::Viewer() :
  GenericWindow(hiddenDevices)
{
  mGeneralInformationWidget = new GeneralInformationWidget(this);
  mSpeedWidget              = new SpeedWidget(this);
  mSteeringWidget           = new SteeringWidget(this);
  mEncodersWidget           = new EncodersWidget(this);
  mBrakeWidget              = new BrakeWidget(this);
  mThrottleWidget           = new ThrottleWidget(this);
  mRPMWidget                = new RPMWidget(this);
  if (QDir(qgetenv("WEBOTS_HOME") + QString("/resources/osm_importer/osm_gui")).exists())
    mOSMImportWidget        = new OSMImportWidget(this);
  else
    mOSMImportWidget = NULL;

  mTabWidget->insertTab(0, mGeneralInformationWidget, "Overview");
  mTabWidget->insertTab(1, mSpeedWidget, "Speed");
  mTabWidget->insertTab(2, mSteeringWidget, "Steering");
  mTabWidget->insertTab(3, mEncodersWidget, "Encoders");
  mTabWidget->insertTab(4, mBrakeWidget, "Brake");
  mTabWidget->insertTab(5, mThrottleWidget, "Throttle");
  mTabWidget->insertTab(6, mRPMWidget, "RPM");

  if (mOSMImportWidget)
    mTabWidget->addTab(mOSMImportWidget, "OSM import");

  mTabWidget->setCurrentIndex(0);
  setMinimumHeight(550);
}

Viewer::~Viewer() {
}

void Viewer::readSensors() {
  mGeneralInformationWidget->updateInformation();
  mSpeedWidget->update();
  mSteeringWidget->update();
  mEncodersWidget->update();
  mBrakeWidget->update();
  mThrottleWidget->update();
  mRPMWidget->update();
  webotsQtUtils::GenericWindow::readSensors();
}

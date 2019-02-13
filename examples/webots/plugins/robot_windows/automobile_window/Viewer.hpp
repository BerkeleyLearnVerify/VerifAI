/*
 * Description:  Add tabs specific to the Car PROTO (and libraries)
 */

#ifndef VIEWER_HPP
#define VIEWER_HPP

class GeneralInformationWidget;
class SpeedWidget;
class SteeringWidget;
class EncodersWidget;
class BrakeWidget;
class ThrottleWidget;
class RPMWidget;
class OSMImportWidget;

#include <gui/GenericWindow.hpp>

class Viewer : public webotsQtUtils::GenericWindow
{
  public:
             Viewer();
    virtual ~Viewer();

    void readSensors();
  private:

    GeneralInformationWidget *mGeneralInformationWidget;
    SpeedWidget              *mSpeedWidget;
    SteeringWidget           *mSteeringWidget;
    EncodersWidget           *mEncodersWidget;
    BrakeWidget              *mBrakeWidget;
    ThrottleWidget           *mThrottleWidget;
    RPMWidget                *mRPMWidget;
    OSMImportWidget          *mOSMImportWidget;
};

#endif

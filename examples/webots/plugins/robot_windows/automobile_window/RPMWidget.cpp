#include "RPMWidget.hpp"

#include <graph2d/Point2D.hpp>

#include <webots/robot.h>
#include <webots/vehicle/driver.h>

using namespace std;

RPMWidget::RPMWidget(QWidget *parent): AbstractWidget(parent)
{
  mGraph->setYLabel("motor RPM");
}

RPMWidget::~RPMWidget() {
}

void RPMWidget::update() {
  if (!mEnableCheckBox->isChecked())
    return;

  if (wbu_driver_get_control_mode() == TORQUE) {
    double rpm = wbu_driver_get_rpm();
    mValueLabel->setText(QString::number(rpm, 'f', 1));
    mGraph->addPoint2D(Point2D(wb_robot_get_time(), rpm));
    mGraph->updateXRange();
    mGraph->extendYRange();
    mGraph->keepNPoints(pointsKeptNumber());
  } else
    mValueLabel->setText("No engine model in speed control");
}

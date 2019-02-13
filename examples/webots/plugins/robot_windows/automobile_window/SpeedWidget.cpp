#include "SpeedWidget.hpp"

#include <graph2d/Point2D.hpp>

#include <webots/robot.h>
#include <webots/vehicle/driver.h>

using namespace std;

SpeedWidget::SpeedWidget(QWidget *parent): AbstractWidget(parent)
{
  mGraph->setYLabel("Speed [km/h]");
  mValueLabel->setText("\n\n");
}

SpeedWidget::~SpeedWidget() {
}

void SpeedWidget::update() {
  if (!mEnableCheckBox->isChecked())
    return;

  mValueLabel->setText("");

  if (wbu_driver_get_control_mode() == SPEED) {
    double targetSpeed = wbu_driver_get_target_cruising_speed();
    mGraph->addPoint2D(Point2D(wb_robot_get_time(), targetSpeed, red()));
    mValueLabel->setText("<font color='red'>Target speed: " + QString::number(targetSpeed, 'f', 2) + QString(" km/h</font><br>"));
  }

  double speed = wbu_driver_get_current_speed();
  mValueLabel->setText( mValueLabel->text() + QString("Current speed: ") + QString::number(speed, 'f', 2) + QString(" km/h"));
  mGraph->addPoint2D(Point2D(wb_robot_get_time(), speed));
  mGraph->updateXRange();
  mGraph->extendYRange();
  mGraph->keepNPoints(2 * pointsKeptNumber());
}

#include "SteeringWidget.hpp"

#include <graph2d/Point2D.hpp>

#include <webots/robot.h>
#include <webots/vehicle/driver.h>
#include <webots/vehicle/car.h>

using namespace std;

SteeringWidget::SteeringWidget(QWidget *parent): AbstractWidget(parent)
{
  mGraph->setYLabel("Steering [rad]");
  mValueLabel->setText("\n\n\n");
}

SteeringWidget::~SteeringWidget() {
}

void SteeringWidget::update() {
  if (!mEnableCheckBox->isChecked())
    return;

  double steering = wbu_driver_get_steering_angle();
  double steeringRight = wbu_car_get_right_steering_angle();
  double steeringLeft = wbu_car_get_left_steering_angle();

  mValueLabel->setText(QString("<font color='red'>Steering angle:") + QString::number(steering, 'f', 4) + QString(" rad</font><br>") +
                       QString("<font color='blue'>Right steering angle:") + QString::number(steeringRight, 'f', 4) + QString(" rad</font><br>") +
                       QString("<font color='green'>Left steering angle:") + QString::number(steeringLeft, 'f', 4) + QString(" rad</font>"));

  mGraph->addPoint2D(Point2D(wb_robot_get_time(), steering, red()));
  mGraph->addPoint2D(Point2D(wb_robot_get_time(), steeringRight, blue()));
  mGraph->addPoint2D(Point2D(wb_robot_get_time(), steeringLeft, green()));
  mGraph->updateXRange();
  mGraph->extendYRange();
  mGraph->keepNPoints(3 * pointsKeptNumber());
}

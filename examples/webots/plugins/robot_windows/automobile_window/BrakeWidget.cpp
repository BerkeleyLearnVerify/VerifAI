#include "BrakeWidget.hpp"

#include <graph2d/Point2D.hpp>

#include <webots/robot.h>
#include <webots/vehicle/driver.h>

using namespace std;

BrakeWidget::BrakeWidget(QWidget *parent): AbstractWidget(parent)
{
  mGraph->setYLabel("Brake [%]");
}

BrakeWidget::~BrakeWidget() {
}

void BrakeWidget::update() {
  if (!mEnableCheckBox->isChecked())
    return;

  double brake = wbu_driver_get_brake_intensity();
  mValueLabel->setText(QString::number(brake, 'f', 3));
  mGraph->addPoint2D(Point2D(wb_robot_get_time(), brake));
  mGraph->updateXRange();
  mGraph->extendYRange();
  mGraph->keepNPoints(pointsKeptNumber());
}

#include "EncodersWidget.hpp"

#include <graph2d/Point2D.hpp>

#include <webots/robot.h>
#include <webots/vehicle/car.h>

using namespace std;

EncodersWidget::EncodersWidget(QWidget *parent): AbstractWidget(parent)
{
  mGraph->setYLabel("Encoders [rad]");
  mValueLabel->setText("\n\n\n\n");
}

EncodersWidget::~EncodersWidget() {
}

void EncodersWidget::update() {
  if (!mEnableCheckBox->isChecked())
    return;

  double encoder[WBU_CAR_WHEEL_NB];
  for (int i = WBU_CAR_WHEEL_FRONT_RIGHT; i<WBU_CAR_WHEEL_NB; ++i)
    encoder[i] = wbu_car_get_wheel_encoder(i);

  mValueLabel->setText(QString("<font color='black'>Front right: ") + QString::number(encoder[WBU_CAR_WHEEL_FRONT_RIGHT], 'f', 2) + QString(" rad</font><br>") +
                       QString("<font color='red'>Front left: ") + QString::number(encoder[WBU_CAR_WHEEL_FRONT_LEFT], 'f', 2) + QString(" rad</font><br>") +
                       QString("<font color='green'>Rear right: ") + QString::number(encoder[WBU_CAR_WHEEL_REAR_RIGHT], 'f', 2) + QString(" rad</font><br>") +
                       QString("<font color='blue'>Rear left: ") + QString::number(encoder[WBU_CAR_WHEEL_REAR_LEFT], 'f', 2) + QString(" rad</font><br>"));

  mGraph->addPoint2D(Point2D(wb_robot_get_time(), encoder[WBU_CAR_WHEEL_FRONT_RIGHT], black()));
  mGraph->addPoint2D(Point2D(wb_robot_get_time(), encoder[WBU_CAR_WHEEL_FRONT_LEFT], red()));
  mGraph->addPoint2D(Point2D(wb_robot_get_time(), encoder[WBU_CAR_WHEEL_REAR_RIGHT], blue()));
  mGraph->addPoint2D(Point2D(wb_robot_get_time(), encoder[WBU_CAR_WHEEL_REAR_LEFT], green()));

  mGraph->updateXRange();
  mGraph->extendYRange();
  mGraph->keepNPoints(4 * pointsKeptNumber());
}

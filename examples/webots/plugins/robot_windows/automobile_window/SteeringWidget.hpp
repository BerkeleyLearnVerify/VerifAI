/*
 * Description:  Tab showing the main steering angle and each wheel steering angles.
 */

#ifndef STEERING_WIDGET_HPP
#define STEERING_WIDGET_HPP

#include "AbstractWidget.hpp"

using namespace webotsQtUtils;

class SteeringWidget : public AbstractWidget
{
  public:
                        SteeringWidget(QWidget *parent = 0);
    virtual            ~SteeringWidget();
    void                update();
};

#endif // STEERING_WIDGET_HPP

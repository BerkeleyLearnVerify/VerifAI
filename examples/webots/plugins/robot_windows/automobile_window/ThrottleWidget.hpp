/*
 * Description:  Tab showing (if controlled in torque) the throttle command
 */

#ifndef THROTTLE_WIDGET_HPP
#define THROTTLE_WIDGET_HPP

#include "AbstractWidget.hpp"

using namespace webotsQtUtils;

class ThrottleWidget : public AbstractWidget
{
  public:
                        ThrottleWidget(QWidget *parent = 0);
    virtual            ~ThrottleWidget();
    void                update();
};

#endif // THROTTLE_WIDGET_HPP

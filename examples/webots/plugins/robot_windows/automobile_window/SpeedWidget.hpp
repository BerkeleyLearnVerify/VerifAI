/*
 * Description:  Tab showing the current speed of the car (and the target speed if controlled in speed)
 */

#ifndef SPEED_WIDGET_HPP
#define SPEED_WIDGET_HPP

#include "AbstractWidget.hpp"

using namespace webotsQtUtils;

class SpeedWidget : public AbstractWidget
{
  public:
                        SpeedWidget(QWidget *parent = 0);
    virtual            ~SpeedWidget();
    void                update();
};

#endif // SPEED_WIDGET_HPP

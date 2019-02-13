/*
 * Description:  Tab showing (if controlled in torque) the rotation speed of the motor
 */

#ifndef RPM_WIDGET_HPP
#define RPM_WIDGET_HPP

#include "AbstractWidget.hpp"

using namespace webotsQtUtils;

class RPMWidget : public AbstractWidget
{
  public:
                        RPMWidget(QWidget *parent = 0);
    virtual            ~RPMWidget();
    void                update();
};

#endif // RPM_WIDGET_HPP

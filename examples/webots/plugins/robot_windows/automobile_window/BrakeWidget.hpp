/*
 * Description:  Tab showing the state of the brake command
 */

#ifndef BRAKE_WIDGET_HPP
#define BRAKE_WIDGET_HPP

#include "AbstractWidget.hpp"

using namespace webotsQtUtils;

class BrakeWidget : public AbstractWidget
{
  public:
                        BrakeWidget(QWidget *parent = 0);
    virtual            ~BrakeWidget();
    void                update();
};

#endif // BRAKE_WIDGET_HPP

/*
 * Description:  Tab showing the state of the 4 encoders
 */

#ifndef ENCODERS_WIDGET_HPP
#define ENCODERS_WIDGET_HPP

#include "AbstractWidget.hpp"

using namespace webotsQtUtils;

class EncodersWidget : public AbstractWidget
{
  public:
                        EncodersWidget(QWidget *parent = 0);
    virtual            ~EncodersWidget();
    void                update();
};

#endif // ENCODERS_WIDGET_HPP

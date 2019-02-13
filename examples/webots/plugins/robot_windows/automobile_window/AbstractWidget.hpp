/*
 * Description:  Abstract tab used to build specifi tabs
 */

#ifndef ABSTRACT_WIDGET_HPP
#define ABSTRACT_WIDGET_HPP

#include <QtGui/QtGui>
#include <QtCore/QtCore>
#include <QtWidgets/QtWidgets>

#include <graph2d/Graph2D.hpp>

using namespace webotsQtUtils;

class AbstractWidget : public QWidget
{
  Q_OBJECT

  public:
                        AbstractWidget(QWidget *parent = 0);
    virtual            ~AbstractWidget();
    virtual void        update() = 0;

  public slots:
    void updateEnableCheckBoxText();

  protected:
    webotsQtUtils::Graph2D *mGraph;
    QGridLayout            *mLayout;
    QCheckBox              *mEnableCheckBox;
    QLabel                 *mValueLabel;

    // colors
    static QColor black() { return QColor(  0,   0,   0); }
    static QColor red()   { return QColor(200,  50,  50); }
    static QColor green() { return QColor( 50, 200,  50); }
    static QColor blue()  { return QColor( 50,  50, 200); }

    static int pointsKeptNumber() { return 200; }
};

#endif // ABSTRACT_WIDGET_HPP

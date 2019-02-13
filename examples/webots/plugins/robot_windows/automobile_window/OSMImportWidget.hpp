/*
 * Description:  Tab allowing to generate worlds using the osm importer script
 */

#ifndef OSM_IMPORTER_WIDGET_HPP
#define OSM_IMPORTER_WIDGET_HPP

#include <QtGui/QtGui>
#include <QtCore/QtCore>
#include <QtWidgets/QtWidgets>

class OSMImportWidget : public QWidget
{
  Q_OBJECT

  public:
                        OSMImportWidget(QWidget *parent = 0);
    virtual            ~OSMImportWidget();

  public slots:
    void launchExecutable();

  protected:
    QPushButton  *mPushButton;
    QVBoxLayout  *mLayout;
};

#endif // OSM_IMPORTER_WIDGET_HPP

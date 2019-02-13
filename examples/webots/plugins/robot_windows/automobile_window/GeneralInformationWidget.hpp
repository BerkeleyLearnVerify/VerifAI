/*
 * Description:  Overview tab allowing to have a quick check on the car state
 */

#ifndef GENERAL_INFORMATION_WIDGET_HPP
#define GENERAL_INFORMATION_WIDGET_HPP

#include <QtGui/QtGui>
#include <QtCore/QtCore>
#include <QtWidgets/QtWidgets>

#include <webots/vehicle/car.h>

class GeneralInformationWidget : public QWidget
{
  Q_OBJECT

  public:                        GeneralInformationWidget(QWidget *parent = 0);
    virtual            ~GeneralInformationWidget();
    void                updateInformation();

  public slots:
    void updateEnableCheckBoxText();

  protected:
    virtual void paintEvent(QPaintEvent *event);
    void drawAxes(QPainter &painter);
    void drawSpeed(QPainter &painter);
    void drawDirectionArray(QPainter &painter);
    void drawTypes(QPainter &painter);
    void drawWheels(QPainter &painter);
    void drawWheelsInformation(QPainter &painter);
    void drawGearboxStateOrTargetSpeed(QPainter &painter);

  private:
    void init();

    QCheckBox *mEnableCheckBox;
    QTime      mLastRefreshTime;
    bool       mIsinitialized;

    // drawing positions
    int mCenterPosition[2];
    int mFrontAxisRightPosition[2];  // right front wheel center
    int mFrontAxisLeftPosition[2];   // left front wheel center
    int mFrontAxisCenterPosition[2];
    int mRearAxisRightPosition[2];   // right rear wheel center
    int mRearAxisLeftPosition[2];    // left rear wheel center
    int mRearAxisCenterPosition[2];

    // fix values
    double  mFrontTrack;
    double  mRearTrack;
    double  mWheelBase;
    double  mFrontWheelRadius;
    double  mRearWheelRadius;
    int     mGearNumber;
    QString mTransmissionType;
    QString mEngineType;

    // variable values
    double mSpeed;
    double mSteeringAngle;
    double mRightSteeringAngle;
    double mLeftSteeringAngle;
    double mThrottle;
    double mBrake;
    double mWheelSpeeds[WBU_CAR_WHEEL_NB];
    double mWheelEncoders[WBU_CAR_WHEEL_NB];
    double mRPM;
    double mTargetSpeed;
    int    mGearbox;
    bool   mIsTorqueControl;
};

#endif // GENERAL_INFORMATION_WIDGET_HPP

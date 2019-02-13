#include "AbstractWidget.hpp"

AbstractWidget::AbstractWidget(QWidget *parent):
  QWidget(parent)
{
  mLayout = new QGridLayout(this);

  mEnableCheckBox = new QCheckBox("Disabled", this);
  connect(mEnableCheckBox, &QCheckBox::stateChanged, this, &AbstractWidget::updateEnableCheckBoxText);
  mLayout->addWidget(mEnableCheckBox, 0, 0);

  mValueLabel = new QLabel("", this);
  mLayout->addWidget(mValueLabel, 0, 1, Qt::AlignRight);

  mGraph = new Graph2D(this);
  mGraph->setYRange(0, 0);
  mLayout->addWidget(mGraph, 1, 0, 1, 2);
}

AbstractWidget::~AbstractWidget() {
}

void AbstractWidget::updateEnableCheckBoxText() {
  if (mEnableCheckBox->isChecked())
    mEnableCheckBox->setText("Enabled");
  else {
    mEnableCheckBox->setText("Disabled");
    mValueLabel->setText("");
  }
}

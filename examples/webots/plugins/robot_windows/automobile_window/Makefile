# Webots Makefile system
#
# You may add some variable definitions hereafter to customize the build process
# See documentation in $(WEBOTS_HOME_PATH)/resources/Makefile.include

space :=
space +=
WEBOTS_HOME_PATH=$(subst $(space),\ ,$(strip $(subst \,/,$(WEBOTS_HOME))))

CXX_SOURCES = entry_points.cpp Viewer.cpp AbstractWidget.cpp GeneralInformationWidget.cpp SpeedWidget.cpp RPMWidget.cpp SteeringWidget.cpp EncodersWidget.cpp ThrottleWidget.cpp BrakeWidget.cpp OSMImportWidget.cpp
HPP_FILES_TO_MOC = GeneralInformationWidget.hpp AbstractWidget.hpp OSMImportWidget.hpp

QT = core gui widgets
USE_C_API = true

QT_UTILS = $(WEBOTS_HOME)/resources/projects/libraries/qt_utils
INCLUDE = -I"$(QT_UTILS)"
LIBRARIES = -L"$(QT_UTILS)" -lqt_utils -ldriver -lcar

include $(WEBOTS_HOME_PATH)/resources/Makefile.include

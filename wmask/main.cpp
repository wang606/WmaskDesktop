#include "wmaskmain.h"

#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    WmaskMain w;
    w.show();
    return a.exec();
}

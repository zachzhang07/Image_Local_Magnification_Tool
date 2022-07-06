import sys
from PyQt5 import QtCore, QtMultimedia, QtWidgets, QtGui
from functools import partial

import os
import numpy as np
import cv2

import magnify


def hex2rgb(hex):
    try:
        r = int(hex[1:3], 16)
        g = int(hex[3:5], 16)
        b = int(hex[5:7], 16)
        if hex[0] == '#' and len(hex) == 7 and 0 <= r < 256 and 0 <= g < 256 and 0 <= b < 256:
            return r, g, b
        else:
            return False
    except:
        return False


class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()
        self.ui = magnify.Ui_MainWindow()
        self.initialize()

    # def comboBoxTextCenter(self):
    #     items = self.ui.centralwidget.findChildren(QtWidgets.QComboBox)
    #     for item in items:
    #         item.setEditable(True)
    #         item.lineEdit().setAlignment(QtCore.Qt.AlignCenter)

    def initialize(self):
        self.ui.setupUi(self)

        self.display_ratio = 0.9

        self.image_paths = ''
        self.save_dir = ''

        self.image = None
        self.image_crop = None
        self.image_resize = None
        self.image_preview = None
        self.idx_image = 0

        self.ratioOffset = 0.5 * np.ones((self.ui.spinBox_num.maximum(), 2))
        self.color_history = [0] * self.ui.spinBox_num.maximum()

        for i in range(self.ui.spinBox_num.maximum()):
            self.color_history[i] = eval(f'self.ui.comboBox_color{i + 1}.currentText()')

        for i in range(self.ui.spinBox_num.maximum()):
            comboBox = eval(f'self.ui.comboBox_color{i + 1}')
            comboBox.lineEdit().setPlaceholderText('#hexcode')
            comboBox.lineEdit().setMaxLength(7)

        self.ui.pushButton_upload.clicked.connect(partial(self.upload_images, 'x'))
        self.ui.pushButton_save.clicked.connect(self.save_results)
        # self.ui.pushButton_reset.clicked.connect(partial(self.initialize, True))
        self.ui.pushButton_reset.clicked.connect(self.reset)

        self.ui.spinBox_resX.editingFinished.connect(partial(self.check_cropresize_preview_show_image, 'x'))
        self.ui.spinBox_resY.editingFinished.connect(partial(self.check_cropresize_preview_show_image, 'y'))

        self.ui.spinBox_cropTop.editingFinished.connect(partial(self.check_cropresize_preview_show_image, 'x'))
        self.ui.spinBox_cropBottom.editingFinished.connect(partial(self.check_cropresize_preview_show_image, 'x'))
        self.ui.spinBox_cropLeft.editingFinished.connect(partial(self.check_cropresize_preview_show_image, 'x'))
        self.ui.spinBox_cropRight.editingFinished.connect(partial(self.check_cropresize_preview_show_image, 'x'))

        self.ui.spinBox_intervalX.editingFinished.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.spinBox_intervalY.editingFinished.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.spinBox_border.editingFinished.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.spinBox_linewidth.editingFinished.connect(partial(self.check_preview_show_image, 'x'))

        self.ui.lineEdit_ratio.editingFinished.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.lineEdit_magnification.editingFinished.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.spinBox_num.editingFinished.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.comboBox_location.currentIndexChanged.connect(partial(self.check_preview_show_image, 'x'))

        self.ui.comboBox_color1.currentIndexChanged.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.comboBox_color2.currentIndexChanged.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.comboBox_color3.currentIndexChanged.connect(partial(self.check_preview_show_image, 'x'))
        self.ui.comboBox_color4.currentIndexChanged.connect(partial(self.check_preview_show_image, 'x'))

        self.ui.graphicsView_selectarea.viewport().installEventFilter(self)

        self.check_range('x')

        # if hasattr(self, 'image_path'):
        #     self.upload_images('x')
        # else:
        #     self.image_paths = ''
        #     self.image = None

    def upload_images(self, priority):
        # if not self.image_paths:
        self.image_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open', '.', '*.jpg;;*.png;;All Files(*)')
        # self.image_paths = [r'C:\Users\JuewenPeng\Desktop\fsdownload\bokeh_NR.jpg']
        if len(self.image_paths) != 0:
            self.image = cv2.imread(self.image_paths[self.idx_image])
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.check_range(priority)
            self.crop_resize_image()
            self.preview_image()
            self.show_image()

    def save_results(self):
        if self.image_preview is None:
            QtWidgets.QMessageBox.warning(self, 'Message', 'No images to save!', QtWidgets.QMessageBox.Ok)
            return
        self.save_dir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Choose directory to save', '.')
        if self.save_dir == '':
            return

        for i in range(len(self.image_paths)):
            image_path = self.image_paths[i]
            image_name = os.path.splitext(os.path.split(image_path)[1])[0]
            self.image = cv2.imread(image_path)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.check_range('x')
            self.crop_resize_image()
            self.preview_image()
            save_path = os.path.join(self.save_dir, self.ui.lineEdit_prefix.text() + image_name + self.ui.lineEdit_suffix.text())
            cv2.imwrite(save_path, cv2.cvtColor(self.image_preview.astype(np.uint8), cv2.COLOR_RGB2BGR))

        QtWidgets.QMessageBox.information(self, 'Message', 'Done saving!', QtWidgets.QMessageBox.Ok)

    def reset(self):
        reply = QtWidgets.QMessageBox.question(self, 'Message', 'Aro you sure to reset?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return
        self.ui.lineEdit_prefix.setText('mag_')
        self.ui.lineEdit_suffix.setText('.jpg')
        self.ui.spinBox_resX.setValue(720)
        self.ui.spinBox_resY.setValue(720)
        self.ui.spinBox_cropTop.setValue(0)
        self.ui.spinBox_cropBottom.setValue(0)
        self.ui.spinBox_cropLeft.setValue(0)
        self.ui.spinBox_cropRight.setValue(0)
        self.ui.spinBox_intervalX.setValue(5)
        self.ui.spinBox_intervalY.setValue(5)
        self.ui.spinBox_border.setValue(0)
        self.ui.spinBox_linewidth.setValue(8)
        self.ui.lineEdit_ratio.setText('1.5')
        self.ui.lineEdit_magnification.setText('4.0')
        self.ui.spinBox_num.setValue(2)
        self.ui.pushButton_locate1.setChecked(True)
        self.ui.comboBox_color1.setCurrentIndex(0)
        self.ui.comboBox_color2.setCurrentIndex(1)
        self.ui.comboBox_color3.setCurrentIndex(2)
        self.ui.comboBox_color4.setCurrentIndex(3)

        self.check_cropresize_preview_show_image('x')


    def check_cropresize_preview_show_image(self, priority):
        self.check_range(priority)
        self.crop_resize_image()
        self.preview_image()
        self.show_image()

    def check_preview_show_image(self, priority):
        self.check_range(priority)
        self.preview_image()
        self.show_image()


    def check_range(self, priority):
        # resolution
        if self.ui.spinBox_resX.value() < 128:
            self.ui.spinBox_resX.setValue(128)
        elif self.ui.spinBox_resX.value() > 4096:
            self.ui.spinBox_resX.setValue(4096)

        if self.ui.spinBox_resY.value() < 128:
            self.ui.spinBox_resY.setValue(128)
        elif self.ui.spinBox_resY.value() > 4096:
            self.ui.spinBox_resY.setValue(4096)

        # crop ratio
        if self.ui.spinBox_cropTop.value() < 0:
            self.ui.spinBox_cropTop.setValue(0)
        elif self.ui.spinBox_cropTop.value() > 80:
            self.ui.spinBox_cropTop.setValue(80)

        if self.ui.spinBox_cropBottom.value() < 0:
            self.ui.spinBox_cropBottom.setValue(0)
        elif self.ui.spinBox_cropBottom.value() > 80:
            self.ui.spinBox_cropBottom.setValue(80)

        if self.ui.spinBox_cropLeft.value() < 0:
            self.ui.spinBox_cropLeft.setValue(0)
        elif self.ui.spinBox_cropLeft.value() > 80:
            self.ui.spinBox_cropLeft.setValue(80)

        if self.ui.spinBox_cropRight.value() < 0:
            self.ui.spinBox_cropRight.setValue(0)
        elif self.ui.spinBox_cropRight.value() > 80:
            self.ui.spinBox_cropRight.setValue(80)

        if self.ui.spinBox_cropTop.value() + self.ui.spinBox_cropBottom.value() > 90:
            self.ui.spinBox_cropBottom.setValue(90 - self.ui.spinBox_cropTop.value())
        elif self.ui.spinBox_cropLeft.value() + self.ui.spinBox_cropRight.value() > 90:
            self.ui.spinBox_cropRight.setValue(90 - self.ui.spinBox_cropLeft.value())


        if self.image is not None:
            h, w = self.image.shape[:2]
            h_crop = h * (1 - self.ui.spinBox_cropTop.value() / 100 - self.ui.spinBox_cropBottom.value() / 100)
            w_crop = w * (1 - self.ui.spinBox_cropLeft.value() / 100 - self.ui.spinBox_cropRight.value() / 100)
            resX = self.ui.spinBox_resX.value()
            resY = self.ui.spinBox_resY.value()
            if priority == 'x':
                resY = round(h_crop / w_crop * self.ui.spinBox_resX.value())
                if resY < 128:
                    resY = 128
                    resX = round(w_crop / h_crop * resY)
                elif resY > 4096:
                    resY = 4096
                    resX = round(w / h * resY)
            else:
                resX = round(w_crop / h_crop * self.ui.spinBox_resY.value())
                if resX < 128:
                    resX = 128
                    resY = round(h_crop / w_crop * resX)
                elif resX > 4096:
                    resX = 4096
                    resY = round(h_crop / w_crop * resX)
            self.ui.spinBox_resX.setValue(resX)
            self.ui.spinBox_resY.setValue(resY)


        # interval
        if self.ui.spinBox_intervalX.value() < 2:
            self.ui.spinBox_intervalX.setValue(2)
        elif self.ui.spinBox_intervalX.value() > int(0.2 * self.ui.spinBox_resX.value()):
            self.ui.spinBox_intervalX.setValue(int(0.2 * self.ui.spinBox_resX.value()))

        if self.ui.spinBox_intervalY.value() < 2:
            self.ui.spinBox_intervalY.setValue(2)
        elif self.ui.spinBox_intervalY.value() > int(0.2 * self.ui.spinBox_resY.value()):
            self.ui.spinBox_intervalY.setValue(int(0.2 * self.ui.spinBox_resY.value()))

        # border
        if self.ui.spinBox_border.value() < -int(0.5 * max(self.ui.spinBox_resX.value(), self.ui.spinBox_resY.value())):
            self.ui.spinBox_border.setValue(-int(0.5 * max(self.ui.spinBox_resX.value(), self.ui.spinBox_resY.value())))
        elif self.ui.spinBox_border.value() > int(0.3 * max(self.ui.spinBox_resX.value(), self.ui.spinBox_resY.value())):
            self.ui.spinBox_border.setValue(int(0.3 * max(self.ui.spinBox_resX.value(), self.ui.spinBox_resY.value())))

        # linewidth
        if self.ui.spinBox_linewidth.value() < 2:
            self.ui.spinBox_linewidth.setValue(2)
        elif self.ui.spinBox_linewidth.value() > int(0.03 * max(self.ui.spinBox_resX.value(), self.ui.spinBox_resY.value())):
            self.ui.spinBox_linewidth.setValue(int(0.03 * max(self.ui.spinBox_resX.value(), self.ui.spinBox_resY.value())))

        # aspect ratio
        if float(self.ui.lineEdit_ratio.text()) < 0.2:
            self.ui.lineEdit_ratio.setText('0.2')
        elif float(self.ui.lineEdit_ratio.text()) > 5.0:
            self.ui.lineEdit_ratio.setText('5.0')

        # magnification
        if float(self.ui.lineEdit_magnification.text()) < 1.0:
            self.ui.lineEdit_magnification.setText('1.0')
        elif float(self.ui.lineEdit_magnification.text()) > 10.0:
            self.ui.lineEdit_magnification.setText('10.0')

        # mag number
        for i in range(self.ui.spinBox_num.maximum()):
            if i < self.ui.spinBox_num.value():
                eval(f'self.ui.pushButton_locate{i+1}.setEnabled(True)')
                eval(f'self.ui.comboBox_color{i+1}.setEnabled(True)')
            else:
                eval(f'self.ui.pushButton_locate{i+1}.setEnabled(False)')
                eval(f'self.ui.comboBox_color{i+1}.setEnabled(False)')

    def crop_resize_image(self):
        if self.image is None:
            return
        ratioCropTop, ratioCropBottom = self.ui.spinBox_cropTop.value() / 100, self.ui.spinBox_cropBottom.value()/ 100
        ratioCropLeft, ratioCropRight = self.ui.spinBox_cropLeft.value() / 100, self.ui.spinBox_cropRight.value() / 100
        h, w = self.image.shape[:2]
        yStart = round(ratioCropTop * h)
        yEnd = round((1 - ratioCropBottom) * h)
        xStart = round(ratioCropLeft * w)
        xEnd = round((1 - ratioCropRight) * w)
        self.image_crop = self.image[yStart: yEnd, xStart: xEnd]

        resX = self.ui.spinBox_resX.value()
        resY = self.ui.spinBox_resY.value()
        self.image_resize = cv2.resize(self.image_crop, (resX, resY), interpolation=cv2.INTER_LINEAR)

        # if self.image_resize is None:
        # h, w = self.image_crop.shape[:2]
        # if priority == 'x':
        #     resY = round(h / w * self.ui.spinBox_resX.value())
        #     resX = self.ui.spinBox_resX.value()
        #     if resY < 128:
        #         resY = 128
        #         resX = round(w / h * resY)
        #     self.image_resize = cv2.resize(self.image_crop, (resX, resY), interpolation=cv2.INTER_LINEAR)
        #     self.ui.spinBox_resY.setValue(resY)
        # else:
        #     resY = self.ui.spinBox_resY.value()
        #     resX = round(w / h * self.ui.spinBox_resY.value())
        #     if resY > 4096:
        #         resY = 4096
        #         resX = round(w / h * resY)
        #     self.image_resize = cv2.resize(self.image_crop, (resX, resY), interpolation=cv2.INTER_LINEAR)
        #     self.ui.spinBox_resX.setValue(resY)

    def preview_image(self):

        warning = False

        if self.image_resize is None:
            return
        if self.ui.spinBox_num.value() == 0:
            self.image_preview = self.image_resize
            return

        location = int(self.ui.comboBox_location.currentIndex())  # 0: up; 1: down; 2: left; 3: right
        w_resize, h_resize = int(self.ui.spinBox_resX.value()), int(self.ui.spinBox_resY.value())
        ratioCropTop, ratioCropBottom = self.ui.spinBox_cropTop.value() / 100, self.ui.spinBox_cropBottom.value() / 100
        ratioCropLeft, ratioCropRight = self.ui.spinBox_cropLeft.value() / 100, self.ui.spinBox_cropRight.value() / 100
        intervalX, intervalY = int(self.ui.spinBox_intervalX.value()), int(self.ui.spinBox_intervalY.value())
        border = int(self.ui.spinBox_border.value())
        linewidth = int(self.ui.spinBox_linewidth.value())
        linewidthHalf = (linewidth + 1) // 2
        aspectRatioMag = float(self.ui.lineEdit_ratio.text())
        magnification = float(self.ui.lineEdit_magnification.text())
        numMag = int(self.ui.spinBox_num.value())

        if location < 2:
            wMAG_resize = int((w_resize - 2*border - (numMag-1)*intervalX - 2*numMag*linewidthHalf) / numMag)
            hMAG_resize = int(wMAG_resize / aspectRatioMag)
            w_preview = max(w_resize, w_resize - 2*border)
            h_preview = h_resize + hMAG_resize + intervalY + 2*linewidthHalf
        elif location < 4:
            hMAG_resize = int((h_resize - 2*border - (numMag-1)*intervalY - 2*numMag*linewidthHalf) / numMag)
            wMAG_resize = int(hMAG_resize * aspectRatioMag)
            h_preview = max(h_resize, h_resize - 2*border)
            w_preview = w_resize + wMAG_resize + intervalX + 2*linewidthHalf
        else:
            raise NotImplementedError(f'"location={location}" Error!')

        hMag_resize = hMAG_resize / magnification
        wMag_resize = wMAG_resize / magnification

        # if hMag_resize < 1 and wMag_resize < 1:
        #     msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Message', 'The size of the magnified areas are smaller than 1px. Please modify the parameters')
        #     msg_box.exec_()
        #     return

        h_crop, w_crop = self.image_crop.shape[:2]
        wMag_crop = w_crop / w_resize * wMag_resize
        hMag_crop = h_crop / h_resize * hMag_resize

        self.image_preview = 255 * np.ones((h_preview, w_preview, 3))

        # draw original image
        if location == 0:
            self.image_preview[hMAG_resize + intervalY + 2*linewidthHalf:, (w_preview-w_resize)//2: (w_preview-w_resize)//2+w_resize] = self.image_resize
        elif location == 1:
            self.image_preview[:-hMAG_resize - intervalY - 2*linewidthHalf, (w_preview-w_resize)//2: (w_preview-w_resize)//2+w_resize] = self.image_resize
        elif location == 2:
            self.image_preview[(h_preview-h_resize)//2: (h_preview-h_resize)//2+h_resize, wMAG_resize + intervalX + 2*linewidthHalf:] = self.image_resize
        else:
            self.image_preview[(h_preview-h_resize)//2: (h_preview-h_resize)//2+h_resize, :-wMAG_resize - intervalX - 2*linewidthHalf] = self.image_resize

        for idx_mag in range(self.ui.spinBox_num.value()):
            # idx_color = eval(f'self.ui.comboBox_color{idx_mag+1}.currentIndex()')
            text = eval(f'self.ui.comboBox_color{idx_mag+1}.currentText()')

            if text == 'red':
                color = (255, 0, 0)
            elif text == 'green':
                color = (0, 255, 0)
            elif text == 'yellow':
                color = (255, 255, 0)
            elif text == 'blue':
                color = (0, 191, 255)
            elif text == '#aabbcc':
                color = hex2rgb(text)
            else:
                color = hex2rgb(text)
                if color is False:
                    text = self.color_history[idx_mag]
                    if text == 'red':
                        color = (255, 0, 0)
                    elif text == 'green':
                        color = (0, 255, 0)
                    elif text == 'yellow':
                        color = (255, 255, 0)
                    elif text == 'blue':
                        color = (0, 191, 255)
                    else:
                        color = hex2rgb(text)
                    eval(f'self.ui.comboBox_color{idx_mag+1}.removeItem(self.ui.comboBox_color{idx_mag+1}.count() - 1)')
                    eval(f'self.ui.comboBox_color{idx_mag+1}.setCurrentText(text)')

            self.color_history[idx_mag] = text

            ratioOffsetY, ratioOffsetX = self.ratioOffset[idx_mag]

            ratioRelativeOffsetY = (ratioOffsetY - ratioCropTop) / (1 - ratioCropTop - ratioCropBottom)
            ratioRelativeOffsetX = (ratioOffsetX - ratioCropLeft) / (1 - ratioCropLeft - ratioCropRight)

            # draw the frames of magnified areas on the original image
            xCenter = w_resize * ratioRelativeOffsetX
            yCenter = h_resize * ratioRelativeOffsetY

            if location == 0:
                xStart = int(xCenter - wMag_resize//2) + (w_preview-w_resize) // 2
                xEnd = int(xStart + wMag_resize)
                yStart = int(yCenter - hMag_resize//2) + hMAG_resize + intervalY + 2*linewidthHalf
                yEnd = int(yStart + hMag_resize)
            elif location == 1:
                xStart = int(xCenter - wMag_resize//2) + (w_preview-w_resize) // 2
                xEnd = int(xStart + wMag_resize)
                yStart = int(yCenter - hMag_resize//2)
                yEnd = int(yStart + hMag_resize)
            elif location == 2:
                xStart = int(xCenter - wMag_resize//2) + wMAG_resize + intervalX + 2*linewidthHalf
                xEnd = int(xStart + wMag_resize)
                yStart = int(yCenter - hMag_resize//2) + (h_preview-h_resize) // 2
                yEnd = int(yStart + hMag_resize)
            else:
                xStart = int(xCenter - wMag_resize//2)
                xEnd = int(xStart + wMag_resize)
                yStart = int(yCenter - hMag_resize//2) + (h_preview-h_resize) // 2
                yEnd = int(yStart + hMag_resize)

            if xStart < linewidthHalf or yStart < linewidthHalf or xEnd-1 >= w_preview-linewidthHalf or yEnd-1 >= h_preview-linewidthHalf:
                self.ui.textBrowser_message.setText(f'The size or location of "mag {idx_mag+1}" is out of range.')
                warning = True
                continue

            cv2.rectangle(self.image_preview, (xStart, yStart), (xEnd-1, yEnd-1), color, thickness=linewidth)

            # draw magnified areas
            xCenter = w_crop * ratioRelativeOffsetX
            yCenter = h_crop * ratioRelativeOffsetY
            xStart = int(xCenter - wMag_crop//2)
            xEnd = int(xStart + wMag_crop)
            yStart = int(yCenter - hMag_crop//2)
            yEnd = int(yStart + hMag_crop)

            mag_crop = self.image_crop[yStart: yEnd, xStart: xEnd]
            mag_resize = cv2.resize(mag_crop, (wMAG_resize, hMAG_resize), interpolation=cv2.INTER_LINEAR)

            if location == 0:
                xStart = max(border, 0) + linewidthHalf + idx_mag * (intervalX + wMAG_resize + 2*linewidthHalf)
                xEnd = xStart + wMAG_resize
                yStart = linewidthHalf
                yEnd = yStart + hMAG_resize
            elif location == 1:
                xStart = max(border, 0) + linewidthHalf + idx_mag * (intervalX + wMAG_resize + 2*linewidthHalf)
                xEnd = xStart + wMAG_resize
                yStart = h_resize + intervalY + linewidthHalf
                yEnd = yStart + hMAG_resize
            elif location == 2:
                xStart = linewidthHalf
                xEnd = xStart + wMAG_resize
                yStart = max(border, 0) + linewidthHalf + idx_mag * (intervalY + hMAG_resize + 2*linewidthHalf)
                yEnd = yStart + hMAG_resize
            else:
                xStart = w_resize + intervalX + linewidthHalf
                xEnd = xStart + wMAG_resize
                yStart = max(border, 0) + linewidthHalf + idx_mag * (intervalY + hMAG_resize + 2*linewidthHalf)
                yEnd = yStart + hMAG_resize

            self.image_preview[yStart: yEnd, xStart: xEnd] = mag_resize
            cv2.rectangle(self.image_preview, (xStart, yStart), (xEnd-1, yEnd-1), color, thickness=linewidth)

        if warning is False:
            self.ui.textBrowser_message.setText('Succeed to magnify.')

    def show_image_in_graphicsview(self, image, graphicsView):
        if image is None:
            return
        h, w = image.shape[:2]

        # graphicsView_preview
        h_graphview = graphicsView.height()
        w_graphview = graphicsView.width()

        display_ratio = self.display_ratio * min(h_graphview / h, w_graphview / w)
        h_adapt = int(display_ratio * h)
        w_adapt = int(display_ratio * w)
        image_adapt = cv2.resize(image, (w_adapt, h_adapt), interpolation=cv2.INTER_LINEAR)

        if image_adapt.dtype == float:
            if image_adapt.max() > 1.01:
                image_adapt = image_adapt.astype(np.uint8)
            else:
                image_adapt = (image_adapt * 255).astype(np.uint8)

        image_qt = QtGui.QImage(image_adapt.data, w_adapt, h_adapt, w_adapt * 3, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(image_qt)
        item = QtWidgets.QGraphicsPixmapItem(pix)
        scene = QtWidgets.QGraphicsScene()
        scene.addItem(item)
        graphicsView.setScene(scene)

    def show_image(self):
        if len(self.image_paths) > 0:
            self.ui.lineEdit_imagename.setText(os.path.split(self.image_paths[self.idx_image])[1])
        self.show_image_in_graphicsview(self.image_resize, self.ui.graphicsView_selectarea)
        self.show_image_in_graphicsview(self.image_preview, self.ui.graphicsView_preview)

    def eventFilter(self, source, event):
        if self.image_resize is not None and self.ui.spinBox_num.value() > 0:
            self.ui.graphicsView_selectarea.setCursor(QtCore.Qt.CrossCursor)
            graphview = self.ui.graphicsView_selectarea
            if event.type() == QtCore.QEvent.MouseButtonPress and source == graphview.viewport():
                # image_h, image_w = self.image_resize.shape[:2]
                y_mouse, x_mouse = event.y(), event.x()
                h_graphview, w_graphview = graphview.height(), graphview.width()
                h, w = self.image_resize.shape[:2]
                display_ratio = self.display_ratio * min(h_graphview / h, w_graphview / w)
                h_adapt = int(display_ratio * h)
                w_adapt = int(display_ratio * w)
                y_point = y_mouse - (h_graphview - h_adapt) // 2
                x_point = x_mouse - (w_graphview - w_adapt) // 2
                ratioRelativeOffsetY = y_point / h_adapt
                ratioRelativeOffsetX = x_point / w_adapt
                # w_resize, h_resize = int(self.ui.spinBox_resX.value()), int(self.ui.spinBox_resY.value())
                # h, w = self.image.shape[:2]
                ratioCropTop, ratioCropBottom = self.ui.spinBox_cropTop.value() / 100, self.ui.spinBox_cropBottom.value() / 100
                ratioCropLeft, ratioCropRight = self.ui.spinBox_cropLeft.value() / 100, self.ui.spinBox_cropRight.value() / 100
                ratioOffsetY = ratioRelativeOffsetY * (1 - ratioCropTop - ratioCropBottom) + ratioCropTop
                ratioOffsetX = ratioRelativeOffsetX * (1 - ratioCropLeft - ratioCropRight) + ratioCropLeft

                idx_mag_select = 0
                for idx_mag in range(self.ui.spinBox_num.value()):
                    if eval(f'self.ui.pushButton_locate{idx_mag+1}.isChecked()'):
                        idx_mag_select = idx_mag
                        break

                self.ratioOffset[idx_mag_select, 0] = ratioOffsetY
                self.ratioOffset[idx_mag_select, 1] = ratioOffsetX

                self.preview_image()
                self.show_image()

        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Q, QtCore.Qt.Key_E]:
            length = len(self.image_paths)
            if length > 0:
                if event.key() == QtCore.Qt.Key_Q:
                    if self.idx_image > 0:
                        self.idx_image -= 1
                    else:
                        self.ui.textBrowser_message.setText('This is the first image.')
                        return
                elif event.key() == QtCore.Qt.Key_E:
                    if self.idx_image < length - 1:
                        self.idx_image += 1
                    else:
                        self.ui.textBrowser_message.setText('This is the last image.')
                        return
                self.image = cv2.imread(self.image_paths[self.idx_image])
                self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                self.check_cropresize_preview_show_image('x')

        elif event.key() in [QtCore.Qt.Key_W, QtCore.Qt.Key_S, QtCore.Qt.Key_A, QtCore.Qt.Key_D]:
            if self.image_resize is not None:
                idx_mag_select = 0
                for idx_mag in range(self.ui.spinBox_num.value()):
                    if eval(f'self.ui.pushButton_locate{idx_mag+1}.isChecked()'):
                        idx_mag_select = idx_mag
                        break
                ratioOffsetX, ratioOffsetY = 0, 0
                w_resize = self.ui.spinBox_resX.value()
                h_resize = self.ui.spinBox_resY.value()
                if w_resize > h_resize:
                    kx = 1
                    ky = w_resize / h_resize * kx
                else:
                    ky = 1
                    kx = h_resize / w_resize * ky
                if event.key() == QtCore.Qt.Key_W:
                    ratioOffsetY = -0.001 * ky
                elif event.key() == QtCore.Qt.Key_S:
                    ratioOffsetY = 0.001 * ky
                elif event.key() == QtCore.Qt.Key_A:
                    ratioOffsetX = -0.001 * kx
                else:
                    ratioOffsetX = 0.001 * kx

                self.ratioOffset[idx_mag_select, 0] += ratioOffsetY
                self.ratioOffset[idx_mag_select, 1] += ratioOffsetX

                self.check_preview_show_image('x')

        elif event.key() == QtCore.Qt.Key_Escape:
            items = self.ui.centralwidget.findChildren(QtWidgets.QWidget)
            for item in items:
                item.clearFocus()

    def resizeEvent(self, event):
        self.show_image()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message', 'Are you sure to quit?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyMainWindow()
    # ui = MyMainWindow()
    # ui.setupUi(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())
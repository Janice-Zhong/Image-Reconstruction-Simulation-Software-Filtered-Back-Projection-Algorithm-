import sys
import numpy as np
from PIL import Image, ImageQt
from scipy.fftpack import fft, fftshift, ifft
from phantominator import shepp_logan
import math
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow,QMessageBox

import Ui_FilterBackProjection  # ui配置文件
import getProjection
import projectionFilter
import backProjection

class myImg():
    isEmpty = True
    N = 128
    theta = None
    projection = None
    img = None
    c0,c1 = (0,0)
    
    
    def shepplogan_ellipse(image_size):
        center = (image_size - 1) / 2
        radius = image_size - center - 1
        norm_radius = math.sqrt(radius**2)
        N_d = 2 * math.ceil(norm_radius)
        return N_d

    def proj(N, N_d, theta):
        shep = np.array([[1, .69, .92, 0, 0, 0],
                        [-.8, .6624, .8740, 0, -.0184, 0],
                        [-.2, .1100, .3100, .22, 0, -18],
                        [-.2, .1600, .4100, -.22, 0, 18],
                        [.1, .2100, .2500, 0, .35, 0],
                        [.1, .0460, .0460, 0, .1, 0],
                        [.1, .0460, .0460, 0, -.1, 0],
                        [.1, .0460, .0230, -.08, -.605, 0],
                        [.1, .0230, .0230, 0, -.606, 0],
                        [.1, .0230, .0460, .06, -.605, 0]])
        # 初始化投影数据P和中间变量
        P = np.zeros((N_d, len(theta)))
        rho = shep[:, 0]
        ae = 0.5 * N * shep[:, 1]
        be = 0.5 * N * shep[:, 2]
        xe = 0.5 * N * shep[:, 3]
        ye = 0.5 * N * shep[:, 4]
        alpha = shep[:, 5] * math.pi / 180
        theta = theta * math.pi / 180
        TT = np.arange(-(N_d-1)/2, (N_d-1)/2 + 1)

        # 循环每个投影角度theta
        for k1 in range(len(theta)):
            P_theta = np.zeros(N_d)
            for k2 in range(np.max(xe.shape)):
                a = (ae[k2] * math.cos(theta[k1] - alpha[k2])) ** 2 + (be[k2] * math.sin(theta[k1] - alpha[k2])) ** 2
                temp = a - (TT - xe[k2] * math.cos(theta[k1]) - ye[k2] * math.sin(theta[k1])) ** 2
                for index in range(len(temp)):
                    if temp[index] > 0:
                        P_theta[index] += rho[k2] * (2 * ae[k2] * be[k2] * math.sqrt(temp[index])) / a
            P[:, k1] = P_theta
        return P
    
    def button1_clicked_success():
        N = int(ui.comboBox.currentText())
        sl_ph = shepp_logan(N)    # 构建shepp_logan
        
        img0 = np.round((sl_ph-np.min(sl_ph))/np.ptp(sl_ph)*255) 
        img = Image.fromarray(img0.astype('uint8'))
        qimg = ImageQt.toqpixmap(img)
        ui.label1.setPixmap(qimg)
        
    def button2_clicked_success():
        N = myImg.N
        theta = np.arange(0,180,180 / N)
        N_ellipse = myImg.shepplogan_ellipse(N)
        proj = myImg.proj(N,N_ellipse,theta)
        
        img0 = np.round((proj-np.min(proj))/np.ptp(proj)*255) 
        img = Image.fromarray(img0.astype('uint8'))
        qimg = ImageQt.toqpixmap(img)
        ui.label2.setPixmap(qimg)
        
        myImg.theta = theta
        myImg.projection = proj
        
    def button3_clicked_success():
        theta = myImg.theta
        filt = projectionFilter.projFilter(myImg.projection)
        iradon = backProjection.backproj(filt, theta)
        img0 = np.round((iradon-np.min(iradon))/np.ptp(iradon)*255) #convert values to integers 0-255
        img = Image.fromarray(img0.transpose().astype('uint8'))
        qimg = ImageQt.toqpixmap(img)
        ui.label3.setPixmap(qimg)
        
    def button4_clicked_success():
        (filepath,filetype) = QFileDialog.getOpenFileName(None,"选取图像文件","./", "*.jpg;*.jpeg;*jfif;;*.png;;*.bmp")
        if filepath == '':
            ui.label.setText("选择文件失败，\n请重新选择！")
            myImg.isEmpty = True
        else:
            myImg.img = Image.open(filepath).convert('L')
            qimg = ImageQt.toqpixmap(myImg.img)
            ui.label1.setScaledContents(True)
            ui.label1.setPixmap(qimg)
            ui.label.setText("读取文件成功！")
            myImg.isEmpty = False
        
    def button5_clicked_success():
        if myImg.isEmpty == True:
            QMessageBox.information(None,"小助手提示您：","未选择图像文件",QMessageBox.Yes, QMessageBox.Yes)
        else:
            myImgPad, myImg.c0, myImg.c1 = getProjection.padImage(myImg.img)
            theta = np.arange(0,181,1)
            sinogram = getProjection.getProj(myImgPad, theta) 
            img = Image.fromarray((sinogram-np.min(sinogram))/np.ptp(sinogram)*255).convert('L')
            qimg = ImageQt.toqpixmap(img)
            ui.label2.setScaledContents(True)
            ui.label2.setPixmap(qimg)
            ui.label.setText("投影成功！")
            myImg.projection = sinogram
            myImg.theta = theta
    
    def button6_clicked_success():
        if myImg.isEmpty == True:
            QMessageBox.information(None,"小助手提示您：","未选择图像文件",QMessageBox.Yes, QMessageBox.Yes)
        else:
            sinogram = myImg.projection
            c0,c1 = (myImg.c0,myImg.c1)
            theta = myImg.theta
            filtSino = projectionFilter.projFilter(sinogram)
            iradon = backProjection.backproj(filtSino, theta)
            iradon2 = np.round((iradon-np.min(iradon))/np.ptp(iradon)*255) #convert values to integers 0-255
            iradonImg = Image.fromarray(iradon2.astype('uint8'))
            n0, n1 = myImg.img.size
            iradonImg = iradonImg.crop((c0, c1, c0+n0, c1+n1))
            qimg = ImageQt.toqpixmap(iradonImg)
            ui.label3.setScaledContents(True)
            ui.label3.setPixmap(qimg)
            ui.label.setText("反投影重建成功！")
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_FilterBackProjection.Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    ui.Button1.clicked.connect(myImg.button1_clicked_success)
    ui.Button2.clicked.connect(myImg.button2_clicked_success)
    ui.Button3.clicked.connect(myImg.button3_clicked_success)
    ui.Button4.clicked.connect(myImg.button4_clicked_success)
    ui.Button5.clicked.connect(myImg.button5_clicked_success)
    ui.Button6.clicked.connect(myImg.button6_clicked_success)
    sys.exit(app.exec_())
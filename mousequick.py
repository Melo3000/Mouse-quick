import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QSpinBox, QComboBox,
                            QPushButton, QCheckBox, QGroupBox, QFormLayout,
                            QLineEdit, QMessageBox, QFileDialog, QInputDialog,
                            QSizePolicy, QStyle)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QKeySequence
import pyautogui
import keyboard
import json

class ClickerThread(QThread):
    """处理鼠标点击的后台线程"""
    update_count = pyqtSignal(int)
    finished = pyqtSignal()
    
    def __init__(self, click_type, interval, count, position_type, x, y, click_method="system"):
        super().__init__()
        self.click_type = click_type
        self.interval = interval
        self.count = count
        self.position_type = position_type
        self.x = x
        self.y = y
        self.running = True
        self.clicks_performed = 0
        self.click_method = click_method  # "system" 或 "direct"
        
    def run(self):
        """执行点击操作"""
        infinite = (self.count == 0)
        count = 0
        
        while (infinite or count < self.count) and self.running:
            # 确定点击位置
            if self.position_type == "固定坐标":
                x, y = self.x, self.y
            else:  # "跟随鼠标"
                x, y = pyautogui.position()
            
            # 执行点击
            if self.click_method == "system":
                # 使用pyautogui进行系统级点击
                self.perform_system_click(x, y)
            else:
                # 使用direct方法直接在当前位置点击
                self.perform_direct_click()
            
            count += 1
            self.clicks_performed = count
            self.update_count.emit(count)
            
            # 间隔等待
            time.sleep(self.interval / 1000.0)
        
        self.finished.emit()
    
    def perform_system_click(self, x, y):
        """使用pyautogui执行系统级点击"""
        if self.click_type == "左键单击":
            pyautogui.click(x=x, y=y, button='left')
        elif self.click_type == "左键双击":
            pyautogui.doubleClick(x=x, y=y, button='left')
        elif self.click_type == "右键单击":
            pyautogui.click(x=x, y=y, button='right')
    
    def perform_direct_click(self):
        """使用鼠标事件直接点击当前位置"""
        import win32api, win32con
        
        # 获取当前鼠标位置
        current_x, current_y = win32api.GetCursorPos()
        
        if self.click_type == "左键单击":
            # 左键单击
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        elif self.click_type == "左键双击":
            # 左键双击
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            time.sleep(0.05)  # 双击间隔
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        elif self.click_type == "右键单击":
            # 右键单击
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
    
    def stop(self):
        """停止点击线程"""
        self.running = False

class MouseClickerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.clicker_thread = None
        self.hotkey = 'f8'  # 默认热键
        self.settings = QSettings("MouseQuick", "Config")
        
        # 设置应用图标 (使用系统鼠标图标)
        self.setWindowIcon(QIcon(self.style().standardIcon(QStyle.SP_ComputerIcon)))
        
        self.initUI()
        self.loadSettings()
        
        # 设置全局热键
        try:
            keyboard.add_hotkey(self.hotkey, self.toggleClicker)
        except Exception as e:
            QMessageBox.warning(self, "热键设置失败", f"默认热键设置失败: {str(e)}\n您可以稍后手动设置热键")
            self.hotkey = ""
        
    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("MouseQuick 鼠标连点器")
        # 移除固定大小设置
        # self.setFixedSize(500, 500)  
        # 改为设置初始大小和最小大小
        self.resize(550, 700)
        self.setMinimumSize(500, 500)
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)  # 增加垂直间距
        main_layout.setContentsMargins(20, 20, 20, 20)  # 增加边距
        
        # 使用策略来设置QGroupBox的大小策略，使其可以随窗口大小变化
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 点击规则设置
        click_group = QGroupBox("点击规则设置")
        click_group.setSizePolicy(size_policy)  # 设置大小策略
        click_layout = QFormLayout()
        click_layout.setSpacing(10)  # 增加表单项间距
        click_layout.setContentsMargins(10, 15, 10, 15)  # 增加内边距
        click_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)  # 允许字段扩展
        
        self.click_type = QComboBox()
        self.click_type.addItems(["左键单击", "左键双击", "右键单击"])
        self.click_type.setMinimumWidth(150)  # 设置下拉框最小宽度
        self.click_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        click_layout.addRow("点击类型:", self.click_type)
        
        self.interval = QSpinBox()
        self.interval.setRange(10, 10000)
        self.interval.setValue(100)
        self.interval.setSuffix(" 毫秒")
        self.interval.setMinimumWidth(150)  # 设置数字框最小宽度
        self.interval.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        click_layout.addRow("点击间隔:", self.interval)
        
        self.click_count = QSpinBox()
        self.click_count.setRange(0, 100000)
        self.click_count.setValue(0)
        self.click_count.setSpecialValueText("无限")
        self.click_count.setMinimumWidth(150)  # 设置数字框最小宽度
        self.click_count.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        click_layout.addRow("点击次数:", self.click_count)
        
        # 添加点击方法选择
        self.click_method = QComboBox()
        self.click_method.addItems(["系统点击", "直接点击(适用于网页)"])
        self.click_method.setMinimumWidth(150)  # 设置下拉框最小宽度
        self.click_method.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        self.click_method.setToolTip("系统点击: 在大多数应用中可用\n直接点击: 适用于网页和某些特殊应用")
        click_layout.addRow("点击方法:", self.click_method)
        
        click_group.setLayout(click_layout)
        main_layout.addWidget(click_group)
        
        # 位置设置
        pos_group = QGroupBox("位置设置")
        pos_group.setSizePolicy(size_policy)  # 设置大小策略
        pos_layout = QFormLayout()
        pos_layout.setSpacing(10)  # 增加表单项间距
        pos_layout.setContentsMargins(10, 15, 10, 15)  # 增加内边距
        pos_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)  # 允许字段扩展
        
        self.position_type = QComboBox()
        self.position_type.addItems(["固定坐标", "跟随鼠标"])
        self.position_type.setMinimumWidth(150)  # 设置下拉框最小宽度
        self.position_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        self.position_type.currentTextChanged.connect(self.updatePositionUI)
        pos_layout.addRow("位置类型:", self.position_type)
        
        coord_layout = QHBoxLayout()
        coord_layout.setSpacing(10)  # 增加水平间距
        
        self.x_coord = QSpinBox()
        self.x_coord.setRange(0, 9999)
        self.x_coord.setValue(500)
        self.x_coord.setMinimumWidth(70)  # 设置数字框最小宽度
        self.x_coord.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        
        self.y_coord = QSpinBox()
        self.y_coord.setRange(0, 9999)
        self.y_coord.setValue(500)
        self.y_coord.setMinimumWidth(70)  # 设置数字框最小宽度
        self.y_coord.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        
        coord_layout.addWidget(QLabel("X:"))
        coord_layout.addWidget(self.x_coord)
        coord_layout.addWidget(QLabel("Y:"))
        coord_layout.addWidget(self.y_coord)
        
        self.get_pos_btn = QPushButton("获取当前位置")
        self.get_pos_btn.setMinimumWidth(100)  # 设置按钮最小宽度
        self.get_pos_btn.clicked.connect(self.getCurrentPosition)
        coord_layout.addWidget(self.get_pos_btn)
        
        pos_layout.addRow("坐标:", coord_layout)
        pos_group.setLayout(pos_layout)
        main_layout.addWidget(pos_group)
        
        # 热键设置
        hotkey_group = QGroupBox("热键设置")
        hotkey_group.setSizePolicy(size_policy)  # 设置大小策略
        hotkey_layout = QHBoxLayout()
        hotkey_layout.setContentsMargins(10, 15, 10, 15)  # 增加内边距
        hotkey_layout.setSpacing(10)  # 增加间距
        
        hotkey_label = QLabel("启动/停止热键:")
        hotkey_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)  # 设置扩展策略
        
        self.hotkey_edit = QLineEdit(self.hotkey)
        self.hotkey_edit.setReadOnly(True)
        self.hotkey_edit.setMinimumWidth(150)  # 设置文本框最小宽度
        self.hotkey_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        self.hotkey_edit.mousePressEvent = self.captureHotkey
        
        hotkey_layout.addWidget(hotkey_label)
        hotkey_layout.addWidget(self.hotkey_edit)
        hotkey_group.setLayout(hotkey_layout)
        main_layout.addWidget(hotkey_group)
        
        # 状态显示
        status_group = QGroupBox("状态")
        status_group.setSizePolicy(size_policy)  # 设置大小策略
        status_layout = QFormLayout()
        status_layout.setContentsMargins(10, 15, 10, 15)  # 增加内边距
        status_layout.setSpacing(10)  # 增加间距
        status_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)  # 允许字段扩展
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        
        self.click_counter = QLabel("0")
        self.click_counter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置扩展策略
        
        status_layout.addRow("状态:", self.status_label)
        status_layout.addRow("已点击次数:", self.click_counter)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)  # 增加按钮间距
        
        self.start_btn = QPushButton("开始")
        self.start_btn.setMinimumSize(120, 40)  # 设置按钮大小
        self.start_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.start_btn.clicked.connect(self.startClicker)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setMinimumSize(120, 40)  # 设置按钮大小
        self.stop_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.stop_btn.clicked.connect(self.stopClicker)
        self.stop_btn.setEnabled(False)
        
        btn_layout.addStretch(1)  # 添加弹性空间使按钮居中
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch(1)  # 添加弹性空间使按钮居中
        main_layout.addLayout(btn_layout)
        
        # 配置保存/加载
        cfg_layout = QHBoxLayout()
        cfg_layout.setSpacing(20)  # 增加按钮间距
        
        self.save_cfg_btn = QPushButton("保存配置")
        self.save_cfg_btn.setMinimumSize(100, 30)  # 设置按钮大小
        self.save_cfg_btn.clicked.connect(self.saveConfig)
        
        self.load_cfg_btn = QPushButton("加载配置")
        self.load_cfg_btn.setMinimumSize(100, 30)  # 设置按钮大小
        self.load_cfg_btn.clicked.connect(self.loadConfig)
        
        cfg_layout.addStretch(1)  # 添加弹性空间使按钮居中
        cfg_layout.addWidget(self.save_cfg_btn)
        cfg_layout.addWidget(self.load_cfg_btn)
        cfg_layout.addStretch(1)  # 添加弹性空间使按钮居中
        main_layout.addLayout(cfg_layout)
        
        # 状态栏
        self.statusBar().showMessage(f"热键 [{self.hotkey}] 可快速开始/停止")
    
    def updatePositionUI(self, position_type):
        """更新位置相关UI的状态"""
        is_fixed = (position_type == "固定坐标")
        self.x_coord.setEnabled(is_fixed)
        self.y_coord.setEnabled(is_fixed)
        self.get_pos_btn.setEnabled(is_fixed)
    
    def getCurrentPosition(self):
        """获取当前鼠标位置"""
        current_pos = pyautogui.position()
        self.x_coord.setValue(current_pos.x)
        self.y_coord.setValue(current_pos.y)
    
    def captureHotkey(self, event):
        """捕获用户输入的热键"""
        # 弹出对话框让用户输入热键
        key, ok = QInputDialog.getText(self, "热键设置", "请按下新的热键，例如：f8, ctrl+b 等:")
        if ok and key:
            try:
                # 测试热键是否有效
                keyboard.parse_hotkey(key)
                
                # 先移除旧热键
                try:
                    keyboard.remove_hotkey(self.hotkey)
                except:
                    pass
                    
                self.hotkey = key
                # 设置新热键
                keyboard.add_hotkey(self.hotkey, self.toggleClicker)
                self.hotkey_edit.setText(self.hotkey)
                self.statusBar().showMessage(f"热键已设置为 [{self.hotkey}]")
            except Exception as e:
                QMessageBox.warning(self, "无效热键", f"设置热键失败: {str(e)}\n请使用有效的热键，如f8、ctrl+b等")
                self.hotkey_edit.setText(self.hotkey)  # 恢复原来的热键显示
    
    def toggleClicker(self):
        """通过热键切换连点器的开始/停止状态"""
        if self.clicker_thread and self.clicker_thread.running:
            self.stopClicker()
        else:
            self.startClicker()
    
    def startClicker(self):
        """开始连点操作"""
        self.status_label.setText("运行中")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 获取选择的点击方法
        click_method = "system" if self.click_method.currentIndex() == 0 else "direct"
        
        # 创建并启动点击线程
        self.clicker_thread = ClickerThread(
            self.click_type.currentText(),
            self.interval.value(),
            self.click_count.value(),
            self.position_type.currentText(),
            self.x_coord.value(),
            self.y_coord.value(),
            click_method
        )
        
        self.clicker_thread.update_count.connect(
            lambda count: self.click_counter.setText(str(count))
        )
        
        self.clicker_thread.finished.connect(self.onClickerFinished)
        self.clicker_thread.start()
        
        # 更新UI状态
        self.click_counter.setText("0")
    
    def stopClicker(self):
        """停止连点操作"""
        if self.clicker_thread and self.clicker_thread.running:
            self.clicker_thread.stop()
            self.clicker_thread.wait()
            self.onClickerFinished()
    
    def onClickerFinished(self):
        """点击操作结束时的处理"""
        self.status_label.setText("就绪")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def saveConfig(self):
        """保存当前配置到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置", "", "配置文件 (*.json)"
        )
        
        if not file_path:
            return
            
        config = {
            "click_type": self.click_type.currentText(),
            "interval": self.interval.value(),
            "click_count": self.click_count.value(),
            "position_type": self.position_type.currentText(),
            "x": self.x_coord.value(),
            "y": self.y_coord.value(),
            "hotkey": self.hotkey,
            "click_method": self.click_method.currentIndex()
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "配置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def loadConfig(self):
        """从文件加载配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载配置", "", "配置文件 (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 应用配置
            self.click_type.setCurrentText(config.get("click_type", "左键单击"))
            self.interval.setValue(config.get("interval", 100))
            self.click_count.setValue(config.get("click_count", 0))
            self.position_type.setCurrentText(config.get("position_type", "跟随鼠标"))
            self.x_coord.setValue(config.get("x", 500))
            self.y_coord.setValue(config.get("y", 500))
            
            # 设置点击方法
            click_method_index = config.get("click_method", 0)
            if 0 <= click_method_index < self.click_method.count():
                self.click_method.setCurrentIndex(click_method_index)
            
            # 更新热键
            saved_hotkey = config.get("hotkey", "f8")
            if saved_hotkey and saved_hotkey != self.hotkey:
                try:
                    # 先移除旧热键
                    if self.hotkey:
                        try:
                            keyboard.remove_hotkey(self.hotkey)
                        except:
                            pass
                    
                    # 测试新热键是否有效
                    keyboard.parse_hotkey(saved_hotkey)
                    self.hotkey = saved_hotkey
                    keyboard.add_hotkey(self.hotkey, self.toggleClicker)
                    self.hotkey_edit.setText(self.hotkey)
                except Exception as e:
                    QMessageBox.warning(self, "热键加载失败", f"保存的热键'{saved_hotkey}'无效: {str(e)}")
                    # 使用默认热键
                    if not self.hotkey:
                        self.hotkey = "f8"
                        try:
                            keyboard.add_hotkey(self.hotkey, self.toggleClicker)
                            self.hotkey_edit.setText(self.hotkey)
                        except:
                            self.hotkey = ""
                            self.hotkey_edit.setText("无热键")
            
            QMessageBox.information(self, "成功", "配置已加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置失败: {str(e)}")
    
    def saveSettings(self):
        """保存应用程序设置"""
        self.settings.setValue("click_type", self.click_type.currentText())
        self.settings.setValue("interval", self.interval.value())
        self.settings.setValue("click_count", self.click_count.value())
        self.settings.setValue("position_type", self.position_type.currentText())
        self.settings.setValue("x", self.x_coord.value())
        self.settings.setValue("y", self.y_coord.value())
        self.settings.setValue("hotkey", self.hotkey)
        self.settings.setValue("click_method", self.click_method.currentIndex())
    
    def loadSettings(self):
        """加载应用程序设置"""
        try:
            self.click_type.setCurrentText(self.settings.value("click_type", "左键单击"))
            self.interval.setValue(int(self.settings.value("interval", 100)))
            self.click_count.setValue(int(self.settings.value("click_count", 0)))
            self.position_type.setCurrentText(self.settings.value("position_type", "跟随鼠标"))
            self.x_coord.setValue(int(self.settings.value("x", 500)))
            self.y_coord.setValue(int(self.settings.value("y", 500)))
            
            # 加载点击方法设置
            click_method_index = int(self.settings.value("click_method", 0))
            if 0 <= click_method_index < self.click_method.count():
                self.click_method.setCurrentIndex(click_method_index)
            
            # 更新热键
            saved_hotkey = self.settings.value("hotkey", "f8")
            if saved_hotkey and saved_hotkey != self.hotkey:
                try:
                    # 先移除旧热键
                    if self.hotkey:
                        try:
                            keyboard.remove_hotkey(self.hotkey)
                        except:
                            pass
                    
                    # 测试新热键是否有效
                    keyboard.parse_hotkey(saved_hotkey)
                    self.hotkey = saved_hotkey
                    keyboard.add_hotkey(self.hotkey, self.toggleClicker)
                    self.hotkey_edit.setText(self.hotkey)
                except Exception as e:
                    QMessageBox.warning(self, "热键加载失败", f"保存的热键'{saved_hotkey}'无效: {str(e)}")
                    # 使用默认热键
                    if not self.hotkey:
                        self.hotkey = "f8"
                        try:
                            keyboard.add_hotkey(self.hotkey, self.toggleClicker)
                            self.hotkey_edit.setText(self.hotkey)
                        except:
                            self.hotkey = ""
                            self.hotkey_edit.setText("无热键")
        except Exception as e:
            QMessageBox.warning(self, "设置加载失败", f"加载设置时出错: {str(e)}")
    
    def closeEvent(self, event):
        """应用程序关闭时的处理"""
        # 停止连点线程
        if self.clicker_thread and self.clicker_thread.running:
            self.clicker_thread.stop()
            self.clicker_thread.wait()
        
        # 保存设置
        self.saveSettings()
        
        # 移除热键
        if self.hotkey:
            try:
                keyboard.remove_hotkey(self.hotkey)
            except:
                pass
        
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MouseClickerApp()
    window.show()
    sys.exit(app.exec_()) 
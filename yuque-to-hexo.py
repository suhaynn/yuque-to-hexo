import sys
import os
import re
import json
import requests
import urllib.parse
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QListWidget, QPushButton,
    QDateEdit, QTextEdit, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import qdarkstyle

class DownloadThread(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool)

    def __init__(self, md_path, front_matter, output_root):
        super().__init__()
        self.md_path = md_path
        self.front_matter = front_matter
        self.output_root = output_root

    def safe_filename(self, filename):
        filename = urllib.parse.unquote(filename)
        filename = os.path.basename(filename).split('?')[0]
        return re.sub(r'[\\/*?:"<>|]', '_', filename)

    def get_unique_path(self, directory, filename):
        counter = 1
        name, ext = os.path.splitext(filename)
        while (directory / filename).exists():
            filename = f"{name}_{counter}{ext}"
            counter += 1
        return directory / filename

    def run(self):
        try:
            original_path = Path(self.md_path)
            folder_name = original_path.stem
            
            # 确定输出根目录
            output_root = Path(self.output_root) if self.output_root else original_path.parent
            output_root.mkdir(parents=True, exist_ok=True)
            
            # 创建目标文件夹
            target_folder = output_root / folder_name
            target_folder.mkdir(exist_ok=True)
            
            # 读取原始内容
            with open(self.md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 处理图片
            image_urls = list(set(re.findall(r'!\[.*?\]\((.*?)\)', content)))
            total_images = len(image_urls)
            processed = 0

            for url in image_urls:
                try:
                    parsed_url = urllib.parse.urlparse(url)
                    original_filename = self.safe_filename(parsed_url.path)
                    
                    # 补充扩展名
                    if not os.path.splitext(original_filename)[1]:
                        try:
                            response = requests.head(url, timeout=5, allow_redirects=True)
                            content_type = response.headers.get('Content-Type', '').split('/')[-1]
                            if content_type in ['jpeg', 'png', 'gif', 'webp']:
                                original_filename += f".{content_type}"
                            else:
                                original_filename += ".png"
                        except:
                            original_filename += ".png"
                    
                    save_path = self.get_unique_path(target_folder, original_filename)
                    
                    # 下载图片
                    response = requests.get(url, stream=True, timeout=10)
                    if response.status_code == 200:
                        with open(save_path, 'wb') as img_file:
                            for chunk in response.iter_content(1024):
                                if chunk:
                                    img_file.write(chunk)
                        content = content.replace(url, save_path.name)
                        self.progress.emit(f"✅ 下载成功: {save_path.name}", int((processed+1)/total_images*100))
                        processed += 1
                    else:
                        self.progress.emit(f"❌ 下载失败: HTTP {response.status_code}", 0)
                except Exception as e:
                    self.progress.emit(f"❌ 下载失败: {str(e)}", 0)

            # 添加Front Matter
            front_matter = '---\n'
            for key, value in self.front_matter.items():
                if isinstance(value, list):
                    value = f"[{', '.join(value)}]"
                front_matter += f"{key}: {value}\n"
            front_matter += '---\n\n'
            content = front_matter + content
            
            # 保存处理后的文件
            output_path = output_root / f"{folder_name}.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.finished.emit(True)
        except Exception as e:
            self.progress.emit(f"💥 处理失败: {str(e)}", 0)
            self.finished.emit(False)

class HexoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.default_output = r"C:\GithubBlog\GithubBlog\source\_posts"  # 默认输出路径
        self.init_ui()
        self.load_config()
        self.current_file = None

    def init_ui(self):
        self.setWindowTitle("yuque-to-hexo By suhaynn")
        self.setAcceptDrops(True)
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 输出路径设置
        output_group = QWidget()
        output_layout = QHBoxLayout(output_group)
        output_layout.addWidget(QLabel("输出路径（置空则保存在当前目录下）:"))
        
        self.output_combo = QComboBox()
        self.output_combo.setEditable(True)
        self.output_combo.setToolTip("输入或选择输出目录，留空则使用当前目录")
        self.output_combo.addItem(self.default_output)  # 确保此时 self.default_output 已定义
        self.output_combo.addItem("选择其他目录...")
        self.output_combo.currentIndexChanged.connect(self.on_output_combo_changed)
        
        output_layout.addWidget(self.output_combo)
        layout.addWidget(output_group)

        # 文件区域
        file_group = QWidget()
        file_layout = QVBoxLayout(file_group)
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(100)
        file_layout.addWidget(QLabel("拖入MD文件或点击选择:"))
        file_layout.addWidget(self.file_list)
        layout.addWidget(file_group)
        
        # 元数据区域
        meta_group = QWidget()
        meta_layout = QVBoxLayout(meta_group)
        
        self.title_input = QLineEdit()
        meta_layout.addWidget(QLabel("文章标题:"))
        meta_layout.addWidget(self.title_input)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        meta_layout.addWidget(QLabel("发布日期:"))
        meta_layout.addWidget(self.date_input)
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        meta_layout.addWidget(QLabel("分类(逗号分隔层级):"))
        meta_layout.addWidget(self.category_combo)
        
        self.tags_input = QLineEdit()
        meta_layout.addWidget(QLabel("标签(逗号分隔):"))
        meta_layout.addWidget(self.tags_input)
        layout.addWidget(meta_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # 处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.process_btn)
        
        # 日志输出
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        
        # 样式设置
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + """
            QProgressBar {
                border: 2px solid #3A3A3A;
                border-radius: 5px;
                height: 20px;
                background: #2B2B2B;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 #5CD6FF,
                    stop:1 #0099CC
                );
                border-radius: 3px;
            }
        """)

    def on_output_combo_changed(self, index):
        if index == 1:  # 选择"选择其他目录..."
            directory = QFileDialog.getExistingDirectory(self, "选择输出目录", self.default_output)
            if directory:
                self.output_combo.insertItem(0, directory)
                self.output_combo.setCurrentIndex(0)
            else:
                self.output_combo.setCurrentIndex(0)

    def get_output_path(self):
        current_text = self.output_combo.currentText().strip()
        if current_text == "选择其他目录...":
            return ""
        return current_text if current_text else None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.md'):
                self.file_list.addItem(path)
                if not self.current_file:
                    self.current_file = path
                    self.title_input.setText(Path(path).stem)

    def load_config(self):
        self.config_file = Path("hexo_editor_config.json")
        default_config = {'categories': [], 'tags': []}
        
        try:
            if self.config_file.exists() and self.config_file.stat().st_size > 0:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = default_config
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f)
        except Exception as e:
            config = default_config
            QMessageBox.warning(self, "配置错误", f"加载配置失败: {str(e)}")

        config.setdefault('categories', [])
        config.setdefault('tags', [])
        
        self.category_combo.clear()
        self.category_combo.addItems(config['categories'])
        if config['tags']:
            self.tags_input.setText(", ".join(config['tags']))

    def save_config(self):
        config = {
            'categories': list({self.category_combo.itemText(i) for i in range(self.category_combo.count())}),
            'tags': [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()]
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_front_matter(self):
        return {
            'title': self.title_input.text() or Path(self.current_file).stem,
            'date': self.date_input.date().toString("yyyy-MM-dd"),
            'categories': [x.strip() for x in self.category_combo.currentText().split(',') if x.strip()],
            'tags': [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()]
        }

    def start_processing(self):
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先选择MD文件!")
            return
        
        self.save_config()
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.log_output.clear()
        
        output_root = self.get_output_path()
        if output_root and not Path(output_root).exists():
            try:
                Path(output_root).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建输出目录: {str(e)}")
                return
        
        for i in range(self.file_list.count()):
            md_path = self.file_list.item(i).text()
            self.current_file = md_path
            self.worker = DownloadThread(md_path, self.get_front_matter(), output_root)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()

    def update_progress(self, message, percent):
        self.progress_bar.setValue(percent)
        self.log_output.append(message)
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.End)
        self.log_output.setTextCursor(cursor)
        self.log_output.ensureCursorVisible()

    def on_finished(self, success):
        if success:
            self.log_output.append("🎉 处理完成！")
            self.progress_bar.hide()
        else:
            self.log_output.append("❌ 处理过程中发生错误！")
            self.progress_bar.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HexoEditor()
    window.show()
    sys.exit(app.exec_())
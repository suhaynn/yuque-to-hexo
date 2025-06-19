# -*- coding: utf-8 -*-
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
    QDateEdit, QTextEdit, QMessageBox, QProgressBar, QGroupBox,
    QSizePolicy, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QFontDatabase
import qdarkstyle


class DownloadThread(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool)

    def __init__(self, md_path, front_matter, output_root, image_url_prefix):
        super().__init__()
        self.md_path = md_path
        self.front_matter = front_matter
        self.output_root = output_root
        self.image_url_prefix = image_url_prefix

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

    def is_valid_url(self, url):
        """检查 URL 是否有效（包含协议头）"""
        return url.startswith(('http://', 'https://'))

    def run(self):
        try:
            original_path = Path(self.md_path)
            folder_name = original_path.stem

            # 确定输出根目录（博客根目录/source/_posts）
            output_root = Path(self.output_root) if self.output_root else original_path.parent
            posts_dir = output_root / "source" / "_posts"
            posts_dir.mkdir(parents=True, exist_ok=True)

            # 创建目标文件夹（在source/_posts/example）
            target_folder = posts_dir / folder_name
            target_folder.mkdir(exist_ok=True)

            # 读取原始内容
            with open(self.md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 处理图片
            image_urls = list(set(re.findall(r'!\[.*?\]\((.*?)\)', content)))
            total_images = len(image_urls)
            processed = 0
            failed_images = []

            for url in image_urls:
                try:
                    # 检查 URL 是否有效
                    download_url = url
                    if not self.is_valid_url(url) and self.image_url_prefix:
                        # 如果 URL 无协议头，尝试补充前缀
                        download_url = urllib.parse.urljoin(self.image_url_prefix, url)
                        self.progress.emit(f"补充 URL 前缀: {url} -> {download_url}", 0)

                    parsed_url = urllib.parse.urlparse(download_url)
                    original_filename = self.safe_filename(parsed_url.path)

                    # 补充扩展名
                    if not os.path.splitext(original_filename)[1]:
                        try:
                            response = requests.head(download_url, timeout=5, allow_redirects=True)
                            content_type = response.headers.get('Content-Type', '').split('/')[-1]
                            if content_type in ['jpeg', 'png', 'gif', 'webp']:
                                original_filename += f".{content_type}"
                            else:
                                original_filename += ".png"
                        except:
                            original_filename += ".png"

                    save_path = self.get_unique_path(target_folder, original_filename)

                    # 下载图片
                    response = requests.get(download_url, stream=True, timeout=10)
                    if response.status_code == 200:
                        with open(save_path, 'wb') as img_file:
                            for chunk in response.iter_content(1024):
                                if chunk:
                                    img_file.write(chunk)
                        # 使用相对路径替换图片链接，如 example/image.jpg
                        relative_path = f"{folder_name}/{save_path.name}"
                        content = content.replace(url, relative_path)
                        self.progress.emit(f"✅ 下载成功: {save_path.name}", int((processed + 1) / total_images * 100))
                        processed += 1
                    else:
                        failed_images.append(url)
                        self.progress.emit(f"❌ 下载失败: HTTP {response.status_code} for {download_url}", 0)
                except Exception as e:
                    failed_images.append(url)
                    self.progress.emit(f"❌ 下载失败: {str(e)} for {download_url}", 0)

            # 如果有下载失败的图片，警告用户
            if failed_images:
                self.progress.emit(f"⚠️ 警告: {len(failed_images)} 张图片下载失败，原始路径已保留", 0)

            # 添加Front Matter
            front_matter = '---\n'
            for key, value in self.front_matter.items():
                if isinstance(value, list):
                    value = f"[{', '.join(value)}]"
                front_matter += f"{key}: {value}\n"
            front_matter += '---\n\n'
            content = front_matter + content

            # 保存处理后的文件（到source/_posts）
            output_path = posts_dir / f"{folder_name}.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.finished.emit(True)
        except Exception as e:
            self.progress.emit(f"💥 处理失败: {str(e)}", 0)
            self.finished.emit(False)


class HexoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.default_root = r"E:\blog\suhaynn"
        self.config = {'categories': [], 'tags': []}
        self.load_config()
        self.init_ui()
        self.current_file = None

    def init_ui(self):
        self.setWindowTitle("yuque-to-hexo By suhaynn")
        self.setAcceptDrops(True)
        self.setGeometry(100, 100, 1000, 800)  # 增大窗口尺寸

        # 加载等宽字体
        font_db = QFontDatabase()
        font_id = font_db.addApplicationFont(":/fonts/RobotoMono-Regular.ttf")
        if font_id != -1:
            self.mono_font = QFont(font_db.applicationFontFamilies(font_id)[0], 10)
        else:
            self.mono_font = QFont("Courier New", 10)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 使用分割器实现可调整区域
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # 上部区域 - 设置部分
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(15)

        # 博客根目录设置
        output_group = QGroupBox("博客根目录设置")
        output_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output_layout = QHBoxLayout(output_group)

        output_label = QLabel("博客根目录（置空则保存在当前目录下）:")
        output_label.setStyleSheet("font-weight: bold;")
        output_layout.addWidget(output_label)

        self.output_combo = QComboBox(self)
        self.output_combo.setEditable(True)
        self.output_combo.setMinimumWidth(400)
        self.output_combo.setToolTip("输入或选择博客根目录，留空则使用当前目录")
        self.output_combo.addItem(self.default_root)
        self.output_combo.addItem("选择其他目录...")
        self.output_combo.currentIndexChanged.connect(self.on_output_combo_changed)
        output_layout.addWidget(self.output_combo)
        settings_layout.addWidget(output_group)

        # 图片 URL 前缀设置
        image_prefix_group = QGroupBox("图片URL设置")
        image_prefix_layout = QHBoxLayout(image_prefix_group)

        image_prefix_label = QLabel("图片URL前缀:")
        image_prefix_label.setStyleSheet("font-weight: bold;")
        image_prefix_layout.addWidget(image_prefix_label)

        self.image_prefix_input = QLineEdit(self)
        self.image_prefix_input.setMinimumWidth(400)
        self.image_prefix_input.setToolTip("输入图片的URL前缀，用于修复无效URL\n例如: https://cdn.yuque.com/")
        self.image_prefix_input.setText("https://cdn.yuque.com/")
        image_prefix_layout.addWidget(self.image_prefix_input)
        settings_layout.addWidget(image_prefix_group)

        # 文件区域
        file_group = QGroupBox("文件处理")
        file_layout = QVBoxLayout(file_group)

        file_label = QLabel("拖入MD文件或点击选择:")
        file_label.setStyleSheet("font-weight: bold;")
        file_layout.addWidget(file_label)

        self.file_list = QListWidget(self)
        self.file_list.setFixedHeight(100)
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        file_layout.addWidget(self.file_list)
        settings_layout.addWidget(file_group)

        # 元数据区域 - 使用水平布局
        meta_group = QGroupBox("文章元数据")
        meta_layout = QHBoxLayout(meta_group)
        meta_layout.setContentsMargins(10, 15, 10, 10)
        meta_layout.setSpacing(15)

        # 左侧 - 基本元数据
        basic_meta_widget = QWidget()
        basic_meta_layout = QVBoxLayout(basic_meta_widget)
        basic_meta_layout.setContentsMargins(0, 0, 0, 0)
        basic_meta_layout.setSpacing(10)

        title_label = QLabel("文章标题:")
        title_label.setStyleSheet("font-weight: bold;")
        basic_meta_layout.addWidget(title_label)

        self.title_input = QLineEdit(self)
        self.title_input.setStyleSheet("padding: 5px;")
        basic_meta_layout.addWidget(self.title_input)

        date_label = QLabel("发布日期:")
        date_label.setStyleSheet("font-weight: bold;")
        basic_meta_layout.addWidget(date_label)

        self.date_input = QDateEdit(self)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet("padding: 5px;")
        basic_meta_layout.addWidget(self.date_input)
        meta_layout.addWidget(basic_meta_widget)

        # 中间 - 分类设置
        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(10)

        category_label = QLabel("分类设置:")
        category_label.setStyleSheet("font-weight: bold;")
        category_layout.addWidget(category_label)

        self.category_list = QListWidget(self)
        self.category_list.setSelectionMode(QListWidget.MultiSelection)
        self.category_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.category_list.itemSelectionChanged.connect(self.update_category_input)
        category_layout.addWidget(self.category_list)

        category_input_label = QLabel("分类(逗号分隔，层级分类):")
        category_input_label.setStyleSheet("font-weight: bold;")
        category_layout.addWidget(category_input_label)

        self.category_input = QLineEdit(self)
        self.category_input.setStyleSheet("padding: 5px;")
        self.category_input.setToolTip("手动输入分类（逗号分隔，层级分类），或从左侧选择")
        category_layout.addWidget(self.category_input)
        meta_layout.addWidget(category_widget)

        # 右侧 - 标签设置
        tags_widget = QWidget()
        tags_layout = QVBoxLayout(tags_widget)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(10)

        tags_label = QLabel("标签设置:")
        tags_label.setStyleSheet("font-weight: bold;")
        tags_layout.addWidget(tags_label)

        self.tags_list = QListWidget(self)
        self.tags_list.setSelectionMode(QListWidget.MultiSelection)
        self.tags_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.tags_list.itemSelectionChanged.connect(self.update_tags_input)
        tags_layout.addWidget(self.tags_list)

        tags_input_label = QLabel("标签(逗号分隔):")
        tags_input_label.setStyleSheet("font-weight: bold;")
        tags_layout.addWidget(tags_input_label)

        self.tags_input = QLineEdit(self)
        self.tags_input.setStyleSheet("padding: 5px;")
        self.tags_input.setToolTip("手动输入标签（逗号分隔），或从左侧选择")
        tags_layout.addWidget(self.tags_input)
        meta_layout.addWidget(tags_widget)

        settings_layout.addWidget(meta_group)
        splitter.addWidget(settings_widget)

        # 下部区域 - 日志输出
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(5, 5, 5, 5)
        log_layout.setSpacing(10)

        # 处理按钮和进度条
        process_group = QWidget()
        process_layout = QHBoxLayout(process_group)
        process_layout.setContentsMargins(0, 0, 0, 0)

        self.process_btn = QPushButton("开始处理", self)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.process_btn.clicked.connect(self.start_processing)
        process_layout.addWidget(self.process_btn)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3A3A3A;
                border-radius: 5px;
                height: 25px;
                background: #2B2B2B;
                text-align: center;
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
        self.progress_bar.hide()
        process_layout.addWidget(self.progress_bar)
        log_layout.addWidget(process_group)

        # 日志输出
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setFont(self.mono_font)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.log_output)
        splitter.addWidget(log_widget)

        # 设置分割器初始比例
        splitter.setSizes([400, 200])

        # 加载分类和标签
        self.load_categories()
        self.load_tags()

        # 应用样式表
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + """
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QLabel {
                padding: 5px 0;
            }
            QLineEdit, QDateEdit, QComboBox {
                padding: 5px;
                border: 1px solid #444;
                border-radius: 4px;
                background: #2B2B2B;
            }
            QSplitter::handle {
                background: #444;
                height: 5px;
            }
        """)

    def on_output_combo_changed(self, index):
        if index == 1:  # 选择"选择其他目录..."
            directory = QFileDialog.getExistingDirectory(self, "选择博客根目录", self.default_root)
            if directory:
                self.output_combo.insertItem(0, directory)
                self.output_combo.setCurrentIndex(0)
                # 重新加载分类和标签
                self.load_categories()
                self.load_tags()
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

    def load_categories(self):
        """从博客根目录的public/categories读取分类"""
        self.category_list.clear()
        output_root = self.get_output_path()
        if output_root:
            categories_path = Path(output_root) / "public" / "categories"
            if categories_path.exists():
                for category in categories_path.iterdir():
                    if category.is_dir():
                        self.category_list.addItem(category.name)
        config_categories = self.config.get('categories', [])
        for category in config_categories:
            if not self.category_list.findItems(category, Qt.MatchExactly):
                self.category_list.addItem(category)

    def load_tags(self):
        """从博客根目录的public/tags读取标签"""
        self.tags_list.clear()
        output_root = self.get_output_path()
        if output_root:
            tags_path = Path(output_root) / "public" / "tags"
            if tags_path.exists():
                for tag in tags_path.iterdir():
                    if tag.is_dir():
                        self.tags_list.addItem(tag.name)
        config_tags = self.config.get('tags', [])
        for tag in config_tags:
            if not self.tags_list.findItems(tag, Qt.MatchExactly):
                self.tags_list.addItem(tag)

    def update_category_input(self):
        """将选中的分类更新到输入框"""
        selected_items = [item.text() for item in self.category_list.selectedItems()]
        self.category_input.blockSignals(True)
        self.category_input.setText(", ".join(selected_items))
        self.category_input.blockSignals(False)

    def update_tags_input(self):
        """将选中的标签更新到输入框"""
        selected_items = [item.text() for item in self.tags_list.selectedItems()]
        self.tags_input.blockSignals(True)
        self.tags_input.setText(", ".join(selected_items))
        self.tags_input.blockSignals(False)

    def load_config(self):
        self.config_file = Path("hexo_editor_config.json")
        default_config = {'categories': [], 'tags': []}

        try:
            if self.config_file.exists() and self.config_file.stat().st_size > 0:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f)
        except Exception as e:
            self.config = default_config
            QMessageBox.warning(self, "配置错误", f"加载配置失败: {str(e)}")

        self.config.setdefault('categories', [])
        self.config.setdefault('tags', [])

    def save_config(self):
        input_categories = [cat.strip() for cat in self.category_input.text().split(',') if cat.strip()]
        list_categories = [self.category_list.item(i).text() for i in range(self.category_list.count())]
        all_categories = list(set(input_categories + list_categories))

        input_tags = [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()]
        list_tags = [self.tags_list.item(i).text() for i in range(self.tags_list.count())]
        all_tags = list(set(input_tags + list_tags))

        config = {
            'categories': all_categories,
            'tags': all_tags
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_front_matter(self):
        return {
            'title': self.title_input.text() or Path(self.current_file).stem,
            'date': self.date_input.date().toString("yyyy-MM-dd"),
            'categories': [x.strip() for x in self.category_input.text().split(',') if x.strip()],
            'tags': [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()]
        }

    def start_processing(self):
        if not hasattr(self, 'file_list') or self.file_list.count() == 0:
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
                QMessageBox.critical(self, "错误", f"无法创建博客根目录: {str(e)}")
                return

        for i in range(self.file_list.count()):
            md_path = self.file_list.item(i).text()
            self.current_file = md_path
            self.worker = DownloadThread(md_path, self.get_front_matter(), output_root,
                                         self.image_prefix_input.text().strip())
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
import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileSystemModel, QTreeView,
    QSplitter, QTextEdit, QFileDialog, QAction, QVBoxLayout,
    QWidget, QPushButton, QPlainTextEdit, QMessageBox
)
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QRegularExpression


class JavaHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        # キーワード → 青 (#0000FF)
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#0000FF"))
        keywords = [
            "abstract", "assert", "boolean", "break", "byte", "case", "catch",
            "char", "class", "const", "continue", "default", "do", "double",
            "else", "enum", "extends", "final", "finally", "float", "for",
            "goto", "if", "implements", "import", "instanceof", "int",
            "interface", "long", "native", "new", "null", "package",
            "private", "protected", "public", "return", "short", "static",
            "strictfp", "super", "switch", "synchronized", "this", "throw",
            "throws", "transient", "try", "void", "volatile", "while"
        ]
        for kw in keywords:
            pattern = QRegularExpression(rf"\b{kw}\b")
            self.rules.append((pattern, keywordFormat))

        # 変数（識別子） → 黒（標準色なので設定なし）

        # 文字列リテラル → 赤 (#A31515)
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor("#A31515"))
        self.rules.append((QRegularExpression(r"\".*\""), stringFormat))


    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Consolas", 12))
        self.highlighter = JavaHighlighter(self.document())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            cursor = self.textCursor()
            cursor.movePosition(cursor.StartOfBlock)
            cursor.select(cursor.LineUnderCursor)
            line = cursor.selectedText()
            indent = len(line) - len(line.lstrip(' '))
            if line.strip().endswith('{'):
                indent += 4
            super().keyPressEvent(event)
            self.insertPlainText(' ' * indent)
        else:
            super().keyPressEvent(event)


class JavaEditorMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Java Editor")
        self.resize(1000, 700)

        self.editor = CodeEditor()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(150)

        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(os.getcwd())
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(os.getcwd()))
        self.tree.clicked.connect(self.open_file)

        splitter = QSplitter()
        splitter.addWidget(self.tree)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.editor)

        self.build_btn = QPushButton("ビルド＆実行")
        self.build_btn.clicked.connect(self.build_and_run)
        right_layout.addWidget(self.build_btn)

        right_layout.addWidget(self.console)
        right_widget.setLayout(right_layout)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 3)

        self.setCentralWidget(splitter)

        self.current_file = None

        menubar = self.menuBar()
        file_menu = menubar.addMenu("ファイル")

        open_action = QAction("開く", self)
        open_action.triggered.connect(self.open_dialog)
        file_menu.addAction(open_action)

        save_action = QAction("保存", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        new_action = QAction("新規作成", self)
        new_action.triggered.connect(self.new_java_file)
        file_menu.addAction(new_action)

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "ファイルを開く", "", "Java Files (*.java)")
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            with open(path, 'r', encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            self.current_file = path
            self.setWindowTitle(f"Java Editor - {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"ファイルを開けませんでした:\n{e}")

    def open_file(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path) and path.endswith(".java"):
            self.load_file(path)

    def save_file(self):
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(self, "名前を付けて保存", "", "Java Files (*.java)")
            if not path:
                return
            self.current_file = path
        try:
            with open(self.current_file, 'w', encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.console.append(f"[✔] 保存しました: {self.current_file}")
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"保存に失敗しました:\n{e}")

    def new_java_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "新規Javaファイル", "", "Java Files (*.java)")
        if path:
            classname = os.path.splitext(os.path.basename(path))[0]
            template = f"""public class {classname} {{
    public static void main(String[] args) {{
        System.out.println("Hello, world!");
    }}
}}"""
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(template)
                self.load_file(path)
            except Exception as e:
                QMessageBox.warning(self, "エラー", f"ファイル作成失敗:\n{e}")

    def build_and_run(self):
        if not self.current_file:
            QMessageBox.warning(self, "警告", "まずファイルを保存してください。")
            return
        self.save_file()

        dir_path = os.path.dirname(self.current_file)
        base_name = os.path.basename(self.current_file)
        class_name = os.path.splitext(base_name)[0]

        compile_cmd = ["javac", base_name]
        run_cmd = ["java", class_name]

        self.console.clear()
        try:
            proc = subprocess.run(compile_cmd, cwd=dir_path, capture_output=True, text=True)
            if proc.returncode != 0:
                self.console.append("[❌] コンパイルエラー:\n" + proc.stderr)
                return
            self.console.append("[✔] コンパイル成功")

            proc = subprocess.run(run_cmd, cwd=dir_path, capture_output=True, text=True)
            self.console.append(proc.stdout)
            if proc.stderr:
                self.console.append(proc.stderr)
        except Exception as e:
            self.console.append(f"[エラー] {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JavaEditorMain()
    window.show()
    sys.exit(app.exec_())

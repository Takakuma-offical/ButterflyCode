# Windows用のUnity C#エディタ（PyQt5版）
# 機能：ファイル読み書き、C#用シンタックスハイライト、タブ対応、ダークモード

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPlainTextEdit, QAction,
    QMessageBox, QTabWidget, QWidget, QVBoxLayout
)
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QRegExp
import sys
import os


class CSharpHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF9D00"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "abstract", "as", "base", "bool", "break", "byte", "case", "catch", "char",
            "checked", "class", "const", "continue", "decimal", "default", "delegate",
            "do", "double", "else", "enum", "event", "explicit", "extern", "false",
            "finally", "fixed", "float", "for", "foreach", "goto", "if", "implicit", "in",
            "int", "interface", "internal", "is", "lock", "long", "namespace", "new",
            "null", "object", "operator", "out", "override", "params", "private",
            "protected", "public", "readonly", "ref", "return", "sbyte", "sealed", "short",
            "sizeof", "stackalloc", "static", "string", "struct", "switch", "this",
            "throw", "true", "try", "typeof", "uint", "ulong", "unchecked", "unsafe",
            "ushort", "using", "virtual", "void", "volatile", "while"
        ]
        self.rules = [(QRegExp(r'\b' + kw + r'\b'), keyword_format) for kw in keywords]

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        self.rules.append((QRegExp("//[^\n]*"), comment_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        self.rules.append((QRegExp("\".*\""), string_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Consolas", 12))
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.highlighter = CSharpHighlighter(self.document())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            cursor = self.textCursor()
            cursor.select(cursor.LineUnderCursor)
            current_line = cursor.selectedText()

            # 現在の行のインデント取得
            indent = ""
            for char in current_line:
                if char in [' ', '\t']:
                    indent += char
                else:
                    break

            # {} に応じてインデントを追加調整
            extra_indent = ""
            if "{" in current_line.strip() and not "}" in current_line:
                extra_indent = "    "  # 4スペース

            super().keyPressEvent(event)  # 通常の改行処理
            self.insertPlainText(indent + extra_indent)
        else:
            super().keyPressEvent(event)


class EditorTab(QWidget):
    def __init__(self, file_path=None):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.editor = CodeEditor()
        self.file_path = file_path
        self.layout.addWidget(self.editor)
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())


class UnityCSharpEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unity C# Editor")
        self.resize(800, 600)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.init_menu()

    def init_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("ファイル")

        open_action = QAction("開く", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("保存", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("名前を付けて保存", self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        new_action = QAction("新規", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        close_action = QAction("終了", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

    def new_file(self):
        editor_tab = EditorTab()
        self.tabs.addTab(editor_tab, "新規")
        self.tabs.setCurrentWidget(editor_tab)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "ファイルを開く", "", "C#ファイル (*.cs);;すべてのファイル (*)")
        if path:
            editor_tab = EditorTab(path)
            filename = os.path.basename(path)
            self.tabs.addTab(editor_tab, filename)
            self.tabs.setCurrentWidget(editor_tab)

    def save_file(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            if current_tab.file_path:
                with open(current_tab.file_path, "w", encoding="utf-8") as f:
                    f.write(current_tab.editor.toPlainText())
            else:
                self.save_file_as()

    def save_file_as(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            path, _ = QFileDialog.getSaveFileName(self, "名前を付けて保存", "", "C#ファイル (*.cs);;すべてのファイル (*)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(current_tab.editor.toPlainText())
                current_tab.file_path = path
                self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = UnityCSharpEditor()
    editor.show()
    sys.exit(app.exec_())


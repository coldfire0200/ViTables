from PyQt5.QtGui import QFont, QTextCursor
from vitables.common.pyqtconsole.console import PythonConsole
import vitables.common.pyqtconsole.highlighter as hl

class QCustomPyQtConsole(PythonConsole):
    dark_theme = {
            'keyword':      hl.format('#569CD6', 'bold'),
            'operator':     hl.format('#C586C0'),
            'brace':        hl.format('#D4D4D4'),
            'defclass':     hl.format('#4EC9B0', 'bold'),
            'function':     hl.format('#9ed72d'),
            'string':       hl.format('#CE9178'),
            'string2':      hl.format('#a79f54'),
            'comment':      hl.format('#4c814f', 'italic'),
            'self':         hl.format('#9CDCFE'),
            'numbers':      hl.format('#b5cda6'),
            'inprompt':     hl.format('#04df02', 'bold'),
            'outprompt':    hl.format('#bcbcbc', 'bold'),
            'default':      hl.format('#dcdc9d'),
            'output':       hl.format('white'),            
            'output-error': hl.format('#fc4503', 'bold'),
            'output-trace': hl.format('#fc9403', 'bold')
        }
    light_theme = {
            'keyword':      hl.format('blue', 'bold'),
            'operator':     hl.format('red'),
            'brace':        hl.format('darkGray'),
            'defclass':     hl.format('black', 'bold'),
            'function':     hl.format('green'),
            'string':       hl.format('magenta'),
            'string2':      hl.format('darkMagenta'),
            'comment':      hl.format('darkGreen', 'italic'),
            'self':         hl.format('black'),
            'numbers':      hl.format('brown'),
            'inprompt':     hl.format('darkBlue', 'bold'),
            'outprompt':    hl.format('darkRed', 'bold'),
            'default':      hl.format('black'),
            'output':       hl.format('black'),            
            'output-error': hl.format('red', 'bold'),
            'output-trace': hl.format('#fc9403', 'bold')
        }

    def __init__(self, parent):
        super().__init__(parent, None)
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(9)
        self.setFont(font)
        self.edit.setStyleSheet('QPlainTextEdit { border: none; }')
        self.set_dark_theme(False)
        self.set_font_size()        
        self.eval_queued()
        self.snapshot_locals = set()
        self.add_locals({'clear': self.clear, 'whos': self.whos, '__console__': self})

    def set_locals(self, locals):
        locals['__console__'] = self
        self.interpreter.locals = locals

    def add_locals(self, locals):
        for key, val in locals.items():
            self.push_local_ns(key, val)
            
    def get_locals(self)->dict:
        return self.interpreter.locals
    
    def set_shortcuts(self, shortcuts):
        self.shortcuts = shortcuts

    def set_dark_theme(self, en):
        theme = QCustomPyQtConsole.dark_theme if en else QCustomPyQtConsole.light_theme
        self.highlighter = hl.PythonHighlighter(self.edit.document(), self._get_input_valid, formats=theme)
        self.pbar.highlighter = hl.PromptHighlighter(formats=theme)

    def set_font_size(self, pointf: float = 10.0):
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSizeF(pointf)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)

    def clear(self):
        self._prompt_pos = 0
        self._prompt_doc = ['']
        self._current_line = -1
        self.clear_input_buffer()
        self.output_lines = set()        
        self.edit.clear()

    def eval(self, source):
        cursor = self._textCursor()
        cursor.movePosition(QTextCursor.End)
        self._setTextCursor(cursor)
        self._hide_cursor()
        self.insert_input_text('\n', show_ps=False)
        self.process_input(source)

    def snapshot(self):
        self.snapshot_locals = set(self.interpreter.locals.keys())
        self.snapshot_locals.add('__builtins__')

    def clear(self, to_be_removed: str|list = None):
        if not to_be_removed:
            for k in list(self.interpreter.locals):
                if k not in self.snapshot_locals:
                    del self.interpreter.locals[k]
        elif isinstance(to_be_removed, list):
            for k in to_be_removed:
                if k in self.interpreter.locals:
                    del self.interpreter.locals[k]
        elif isinstance(to_be_removed, str):
            if to_be_removed in self.interpreter.locals:
                del self.interpreter.locals[to_be_removed]

    def whos(self, *kargs, **kwargs):
        exclude_snapshot = True if 'exclude' not in kwargs else kwargs['exclude']
        enable_print = True if 'print' not in kwargs else kwargs['print']
        all_keys = [k for k in self.interpreter.locals.keys() 
                    if (not exclude_snapshot or k not in self.snapshot_locals)]
        keys = []
        for k in all_keys:
            if not kargs or k in kargs:
                keys.append(k)
                if enable_print:
                    print(f'{k}: {type(self.interpreter.locals[k])}')
        return keys

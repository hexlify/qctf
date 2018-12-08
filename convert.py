import os
from zipfile import ZipFile
from xml.sax import parseString
from xml.sax.handler import ContentHandler

import chardet


class ConversionError(Exception):
    pass


def convert_file(file):
    file_ext = os.path.splitext(file.filename)[1]
    for converter_cls in FileConverter.__subclasses__():
        if file_ext in converter_cls.__extensions__:
            converter = converter_cls()
            try:
                return converter.convert(file)
            except Exception as e:
                raise ConversionError('Ошибка преобразования файла') from e
    else:
        raise ConversionError('Формат файла не поддерживается')


class FileConverter:
    __extensions__ = []

    def convert(self, file):
        pass


class TxtConverter(FileConverter):
    __extensions__ = [".txt"]

    def convert(self, file):
        file_bytes = file.read()
        encoding = chardet.detect(file_bytes)['encoding']
        return file_bytes.decode(encoding, errors='ignore')


class DocxConverter(FileConverter):
    __extensions__ = [".docx"]

    def convert(self, file):
        with ZipFile(file.stream._file) as docx_file:
            with docx_file.open('word/document.xml') as xml_file:
                document = xml_file.read()
                handler = TextExtractor()
                parseString(document, handler=handler)
                return handler.text


class TextExtractor(ContentHandler):
    def __init__(self):
        super().__init__()
        self.text = ""
        self._inside_text_element = False

    def characters(self, content):
        if self._inside_text_element:
            self.text += content

    def startElement(self, name, attrs):
        if name == "w:t":
            self._inside_text_element = True

    def endElement(self, name):
        if name == "w:t":
            self._inside_text_element = False
        if name == "w:p":
            self.text += "\n"

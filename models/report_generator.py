from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm
import datetime
from pathlib import Path

class VibraTableReportGenerator:
    def __init__(self):
        self.data = datetime.datetime.now().strftime('%Y-%m-%d')

    def transform_date(self):
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
               'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        year, month, day = self.data.split('-')
        return f'«{day}» {months[int(month)-1]} {year}'

    def number_protocol(self):
        year, month, day = self.data.split('-')
        return f'ДС-0{month}-{year}-'

    def safe_image(self, path_, width, doc, savedir):
        savedir = Path(savedir)
        path = savedir / path_
        if not path.exists():
            print(f"⚠️ Файл не найден: {path}")
            return ""
        try:
            return InlineImage(doc, str(path), width=width)
        except Exception as e:
            print(f"❌ Ошибка вставки изображения: {e}")
            return ""

    def generate_report(self, name, a, b, h, savedir):
        template_path = Path(__file__).parent.parent / 'VibraTable_Template_DS.docx'
        print(f"🔍 Путь к шаблону: {template_path.resolve()}")

        if not template_path.exists():
            raise FileNotFoundError(f"🚨 Шаблон не найден: {template_path}")

        try:
            doc = DocxTemplate(template_path)
            print("✅ Шаблон загружен")
        except Exception as e:
            raise Exception(f"🚨 Ошибка загрузки шаблона: {e}")

        context = {
            'name': name,
            'test_date': self.transform_date(),
            'a': a,
            'b': b,
            'h': h,
            'num_protocol': self.number_protocol(),
            'load_pic': self.safe_image('Деформация_во_времени.png', Cm(14), doc, savedir),
            'cycles_pic': self.safe_image('Полные_зависимости.png', Cm(14), doc, savedir),
            'elastic_pic': self.safe_image('Основные_графики.png', Cm(14), doc, savedir)
        }

        try:
            doc.render(context)
            output_path = Path(savedir) / '003.docx'
            doc.save(output_path)
            print(f"✅ Документ сохранён: {output_path}")
            return output_path
        except Exception as e:
            raise Exception(f"🚨 Ошибка при сохранении: {e}")
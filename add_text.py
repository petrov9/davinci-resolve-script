import os
import re
from datetime import datetime
from PIL import Image

# Словарь для перевода месяцев
MONTHS_RU = {
    "January": "Январь",
    "February": "Февраль",
    "March": "Март",
    "April": "Апрель",
    "May": "Май",
    "June": "Июнь",
    "July": "Июль",
    "August": "Август",
    "September": "Сентябрь",
    "October": "Октябрь",
    "November": "Ноябрь",
    "December": "Декабрь"
}


def create_black_image() -> str:
    """Создает черное изображение и сохраняет его.
    Если изображение уже существует, функция его просто загружает.
    """

    script_dir = os.path.dirname(os.path.abspath(__name__))
    temp_dir = os.path.join(script_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, 'temp_black.jpg')

    if not os.path.exists(temp_path):  # Проверяем, существует ли файл
        img = Image.new('RGB', (1920, 1080), color='black')
        img.save(temp_path)
        print(f"Black image created and saved to: {temp_path}")  # Информируем о создании
    else:
        print(f"Black image already exists at: {temp_path}")  # Информируем о загрузке

    return temp_path


def get_image_date_from_filename(image_path):
    """Извлекает дату из названия файла изображения."""
    filename = os.path.basename(image_path)  # Получаем только имя файла
    match = re.search(r"(\d{1,2})\s+(\w+)", filename)  # Ищем дату в формате "ДД месяц"
    if match:
        day = int(match.group(1))
        month_name = match.group(2)

        # Словарь для преобразования названия месяца в номер
        month_dict = {
            "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
            "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
        }
        month = month_dict.get(month_name.lower())  # Получаем номер месяца

        if month:
            year = datetime.now().year  # Получаем текущий год
            date_obj = datetime(year, month, day)
            return date_obj
        else:
            raise Exception(f"Некорректное название месяца: {month_name}")
    else:
        raise Exception(f"Формат названия файла не соответствует ожидаемому: {filename}")


def mergeTextAndImage(text, timeline, clip, textYPos):
    # Создаем Fusion композицию для фото
    timeline.CreateFusionClip([clip], 2.0)
    fu = resolve.Fusion()
    resolve.OpenPage('Fusion')
    comp = fu.GetCurrentComp()

    # Получаем MediaIn node
    mediaIn = comp.ActiveTool()

    # Добавляем Text+ node
    text_plus = comp.AddTool("TextPlus")
    text_plus.StyledText = text
    text_plus.FontSize = 50
    text_plus.Center = (0.5, textYPos)  # Текст внизу

    # Добавляем Merge node
    merge = comp.AddTool("Merge")
    merge.Background = mediaIn.Output
    merge.Foreground = text_plus.Output

    # Подключаем к MediaOut
    mediaOut = comp.FindTool("MediaOut1")
    if mediaOut:
        mediaOut.Input = merge.Output

    return merge


def create_month_title_clip(timeline, mediaPool, month_name):
    print(f"Creating title for {month_name}")

    # Импортируем изображение
    temp_black = create_black_image()
    mediaItem = mediaPool.ImportMedia(temp_black)
    if not mediaItem:
        raise Exception(f"Couldn't import image: {temp_black}")

    # mediaItem.SetClipDuration(2 * 24)

    # Добавляем клип в timeline
    mediaPool.AppendToTimeline(mediaItem)

    clip = timeline.GetItemListInTrack("video", 1)[-1]
    # clip.SetProperty("Duration", 2.0)  # Длительность фото 2 секунды

    # Создаем Fusion композицию для фото
    merge = mergeTextAndImage(month_name, timeline, clip, 0.5)

    return merge


def process_image(image_file, mediaPool, timeline):
    # Обработка изображения
    image_path = os.path.join(folder_path, image_file)
    image_text = os.path.splitext(image_file)[0]
    print(f"Processing: {image_file}")

    # Импортируем изображение
    mediaItem = mediaPool.ImportMedia(image_path)
    if not mediaItem:
        raise Exception(f"Couldn't import image: {image_path}")

    # mediaItem[0].SetClipProperty("Duration", "48")
    # mediaItem[0].SetClipProperty("Duration", "00:00:02:00")

    # Добавляем клип в timeline
    mediaPool.AppendToTimeline(mediaItem)
    clip = timeline.GetItemListInTrack("video", 1)[-1]
    clip_name = clip.GetName()

    # Длительность фото 2 секунды
    # clip.SetProperty("Duration", duration_frames)

    # clip.SetTimelineIn(0) # Начало клипа
    # clip.SetTimelineOut(2 * frame_rate) # Конец клипа через 2 секунды

    mergeTextAndImage(image_text, timeline, clip, 0.2)


def process_images(folder_path, mediaPool):
    timeline = mediaPool.CreateEmptyTimeline("PhotosByMonth")

    # Получаем список файлов изображений из папки
    image_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]
    if not image_files:
        raise Exception(f"No images found in {folder_path}")

    # Сортируем файлы по дате
    image_files_with_dates = []
    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)
        date = get_image_date_from_filename(image_path)
        image_files_with_dates.append((image_file, date))
    image_files_with_dates.sort(key=lambda x: x[1])

    # frame_rate = 1
    # frame_rate = timeline.GetSetting("timelineFrameRate")
    # duration_frames = int(2.0 * frame_rate)

    current_month = None

    # Обрабатываем каждое изображение
    for image_file, date in image_files_with_dates:

        month_eng = date.strftime("%B")  # Получаем название месяца на английском
        month = MONTHS_RU[month_eng]  # Переводим на русский

        # Если начался новый месяц, добавляем заголовок
        if month != current_month:
            current_month = month

            # Создаем заголовок месяца
            title_clip = create_month_title_clip(timeline, mediaPool, month)
            if not title_clip:
                raise Exception(f"Failed to create title for {month}")

        process_image(image_file, mediaPool, timeline)

    print("Processing complete!")


def process_image_folder(folder_path):
    # Инициализация Resolve
    projectManager = resolve.GetProjectManager()
    project = projectManager.GetCurrentProject()
    mediaPool = project.GetMediaPool()

    process_images(folder_path, mediaPool)

    # defaultDuration = 2
    # mediaFiles = mediaPool.GetRootFolder().GetSubFolders()[0].GetItems()
    # Перебираем все медиафайлы
    # for mediaFile in mediaFiles.values():
    # Проверяем, является ли медиафайл изображением
    #    if mediaFile.GetMediaType() == "image":
    # Устанавливаем продолжительность изображения
    #        mediaFile.SetClipDuration(defaultDuration * frame_rate)

    # print("Продолжительность всех изображений в Media Pool установлена на", defaultDuration, "секунды.")

    #temp_black = create_black_image()
    #os.remove(temp_black)


# Пример использования:
folder_path = "D:/итоги года/2021-2023/2023/test"  # Укажите путь к вашей папке с фотографиями
process_image_folder(folder_path)

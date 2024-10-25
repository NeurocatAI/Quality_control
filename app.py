# app.py
import streamlit as st
import openai
import os
from utils.transcription import transcribe_audio
from utils.dialogue_formatting import format_dialogue
from utils.quality_control import quality_control
from utils.error_detection import detect_errors
from utils.recommendations import generate_recommendations
from utils.client_questions import extract_client_questions
from utils.save_to_google_sheets import save_to_google_sheets
import tempfile

# Функция для сброса состояния сессии
def reset_session_state():
    for key in ['transcription', 'formatted_dialogue', 'qc_analysis', 'average_score',
                'manager_errors', 'manager_recommendations', 'client_questions',
                'save_success', 'analysis_started']:
        if key in st.session_state:
            del st.session_state[key]

# Получение PIN-кода и ключа API из секретов
USER_PIN = st.secrets["USER_PIN"]

# Проверяем, установлен ли флаг доступа в сессии
if 'access_granted' not in st.session_state:
    st.session_state['access_granted'] = False

# Если доступ не предоставлен, показываем форму ввода PIN-кода
if not st.session_state['access_granted']:
    with st.form(key='pin_form'):
        pin = st.text_input("Введите PIN для доступа", type="password")
        submit_button = st.form_submit_button("Войти")
    if submit_button:
        if pin == USER_PIN:
            st.session_state['access_granted'] = True
            st.success("Доступ разрешен")
        else:
            st.warning("Неверный PIN. Пожалуйста, попробуйте снова.")
            st.stop()
    else:
        st.stop()

# Если доступ предоставлен, показываем остальную часть приложения
if st.session_state['access_granted']:
    # Установка API-ключа
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    openai.api_key = OPENAI_API_KEY

    st.title("Анализ звонков менеджеров")

    # Загрузка аудиофайла
    audio_file = st.file_uploader("Загрузите аудиофайл", type=["mp3", "wav", "m4a"])

    if 'analysis_started' not in st.session_state:
        st.session_state['analysis_started'] = False

    if audio_file is not None:
        if st.button("Начать анализ"):
            reset_session_state()
            st.session_state['analysis_started'] = True
            # Сохраняем загруженный файл во временной директории
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name
            st.session_state['tmp_file_path'] = tmp_file_path
            st.session_state['file_name'] = audio_file.name

    if st.session_state.get('analysis_started', False):
        # Выполняем транскрипцию
        with st.spinner("Транскрибируем аудио..."):
            transcription = transcribe_audio(st.session_state['tmp_file_path'])
            st.session_state['transcription'] = transcription

        # Отображаем транскрипцию под спойлером
        with st.expander("Транскрипция"):
            st.write(st.session_state['transcription'])

        # Форматируем диалог
        with st.spinner("Форматируем диалог..."):
            formatted_dialogue = format_dialogue(st.session_state['transcription'])
            st.session_state['formatted_dialogue'] = formatted_dialogue

        # Отображаем диалог под спойлером
        with st.expander("Диалог"):
            st.write(st.session_state['formatted_dialogue'])
            
            # Критерии оценки
            criteria = """
            1. Установил ли менеджер контакт с клиентом (приветствие, презентация себя исходя из ситуации клиента, обращение по имени). Оценка "1" - да, контакт установил, оценка "0.5" - частично контакт установил, но некоторые пункты упустил, оценка "0" - нет, контакт не был установлен.
            2. Было ли выполнено менеджером программирование на диалог (проговорил структуру диалога, получил согласие от клиента, выяснил откуда узнал о нас клиент, задал вопрос о информации о нас). Оценка "1" да, выполнил програмирование на диалог, оценка "0.5" - частично выполнил програмирование на диалог, но некоторые пункты упустил, оценка "0" - нет, програмирование на диалог не выполнил.
            3. Задал ли менеджер 2 открытых ситуационных вопроса для выявления потребности клиента. Оценка "1" - да, все вопросы заданы, оценка "0.5" - частично, задан всего один ситуационный вопрос, оценка "0" - нет, вопросы не заданы.
            4. Рассчитана ли сумма долга исходя из ежемесячных платежей, сумма по договору, резюмирована ли полная картина по ситуации клиента, произведен ли расчет по удержаниям доходов, если у клиента уже приставы. Оценка "1" - да, выполнено все перечисленное, оценка "0.5" - частично выполнено перечисленное, но некоторые пункты упущены, оценка "0" - нет, не выполнено.
            5. Был ли представлен и подробно описан кейс №1 с именем клиента, суммой долга и полным описанием ситуации. Оценка "1" - да, кейс представлен, оценка "0.5" - кейс представлен частично, упомянут вкратце или без имени клиента, оценка "0" - нет, кейс не представлен.
            6. Выявил ли менеджер боль клиента с помощью открытых вопросов. Оценка "1" - да, боль выявлена, оценка "0.5" - частично выявлена, оценка "0" - нет, боль не выявлена.
            7. Было ли присоединение, эмпатия, усиление боли через кейс №2. Оценка "1" - да, действия выполнены, оценка "0.5" - частично выполнены, оценка "0" - нет, действия не выполнены.
            8. Нарисовал ли менеджер картинку позитивного и негативного будущего, используя боль клиента. Оценка "1" - да, картина нарисована, оценка "0.5" - частично нарисована, оценка "0" - нет, картина не нарисована.
            9. Была ли подробно описана схема банкротства и эффективно представлен кейс №3, привязанный к боли клиента. Оценка "1" - да, схема и кейс представлены, оценка "0.5" - частично представлены, оценка "0" - нет, не представлены.
            10.  Уточнил ли менеджер намерения клиента, задав вопрос "Нравится ли вам идея списать долги?". Оценка "1" - да, вопрос задан, оценка "0" - нет, вопрос не задан.
            10. Уточнил ли менеджер намерения клиента, задав вопрос "Нравится ли вам идея списать долги?". Оценка "1" - да, вопрос задан, оценка "0" - нет, вопрос не задан.
            11. Попытался ли менеджер закрыть клиента на полный платеж или на рассрочку менее 10 месяцев, задав вопрос “За сколько месяцев справились бы с этой суммой?”. Оценка "1" - да, попытка сделана, оценка "0.5" - частично сделана, оценка "0" - нет, попытка не сделана.
            12. Был ли сделан финальный призыв к действию с использованием оффера/боли/проблемы клиента. Оценка "1" - да, призыв сделан, оценка "0.5" - частично сделан, и что-то упущено из оффера/боли/проблемы клиента, оценка "0" - нет, призыв не сделан.
            13. Упомянул ли менеджер партнерскую программу. Оценка "1" - да, партнерская программа упомянута, оценка "0" - нет, программа не упомянута.
            """

        # Контроль качества
        with st.spinner("Проводим контроль качества..."):
            qc_analysis, scores = quality_control(st.session_state['formatted_dialogue'], criteria)
            average_score = sum(scores) / len(scores) if scores else 0
            st.session_state['qc_analysis'] = qc_analysis
            st.session_state['average_score'] = average_score

        # Отображаем анализ качества под спойлером
        with st.expander("Анализ качества и оценки"):
            st.write(st.session_state['qc_analysis'])
            st.write(f"**Средний балл:** {st.session_state['average_score']:.2f}")

        # Определяем ошибки менеджера
        with st.spinner("Определяем ошибки менеджера..."):
            manager_errors = detect_errors(st.session_state['formatted_dialogue'])
            st.session_state['manager_errors'] = manager_errors

        # Отображаем ошибки менеджера под спойлером
        with st.expander("Ошибки менеджера"):
            st.write(st.session_state['manager_errors'])

        # Генерируем рекомендации
        with st.spinner("Формируем рекомендации..."):
            manager_recommendations = generate_recommendations(st.session_state['formatted_dialogue'])
            st.session_state['manager_recommendations'] = manager_recommendations

        # Отображаем рекомендации под спойлером
        with st.expander("Рекомендации"):
            st.write(st.session_state['manager_recommendations'])

        # Извлекаем вопросы клиента
        with st.spinner("Извлекаем вопросы клиента..."):
            client_questions = extract_client_questions(st.session_state['formatted_dialogue'])
            st.session_state['client_questions'] = client_questions

        # Отображаем вопросы клиента под спойлером
        with st.expander("Вопросы клиента"):
            st.write(st.session_state['client_questions'])

        # Сохраняем данные в Google Таблицу
        with st.spinner("Сохраняем данные в Google Таблицу..."):
            success = save_to_google_sheets(
                file_name=st.session_state['file_name'],
                transcription=st.session_state['transcription'],
                call_evaluation=st.session_state['qc_analysis'],
                average_score=st.session_state['average_score'],
                manager_errors=st.session_state['manager_errors'],
                improvement_recommendations=st.session_state['manager_recommendations'],
                client_questions=st.session_state['client_questions']
            )
            st.session_state['save_success'] = success

        # Отображение уведомления о сохранении данных
        if st.session_state['save_success']:
            st.success("Данные успешно сохранены в Google Таблицу.")
        else:
            st.error("Не удалось сохранить данные в Google Таблицу.")

        # Предлагаем проанализировать другой файл
        if st.button("Анализировать другой файл"):
            reset_session_state()
            st.experimental_rerun()

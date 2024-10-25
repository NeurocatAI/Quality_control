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

# Получение PIN-кода и ключа API из секретов
USER_PIN = st.secrets["USER_PIN"]

# Проверяем, введен ли корректный PIN в сессии
if 'access_granted' not in st.session_state:
    st.session_state['access_granted'] = False

if not st.session_state['access_granted']:
    pin = st.text_input("Введите PIN для доступа", type="password")
    if pin:
        if pin == USER_PIN:
            st.session_state['access_granted'] = True
            st.success("Доступ разрешен")
            st.experimental_rerun()  # Перезапускаем приложение
        else:
            st.warning("Неверный PIN. Пожалуйста, попробуйте снова.")
            st.stop()
    else:
        st.stop()
else:
    # Остальной код приложения
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

    # Установка API-ключа
    openai.api_key = OPENAI_API_KEY

    st.title("Анализ звонков менеджеров")

    # Загрузка аудиофайла
    audio_file = st.file_uploader("Загрузите аудиофайл", type=["mp3", "wav", "m4a"])

    if audio_file is not None:
        if st.button("Начать анализ"):
            # Сохраняем загруженный файл во временной директории
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name

            # Получаем имя файла
            file_name = audio_file.name

            # Сохранение имени файла в Google Таблицу (инициализация записи)
            save_to_google_sheets(file_name=file_name)

            # Транскрибирование аудио
            with st.spinner("Транскрибируем аудио..."):
                transcription = transcribe_audio(tmp_file_path)

            st.subheader("Транскрипция")
            st.write(transcription)

            # Сохранение транскрипции
            with st.spinner("Сохраняем транскрипцию..."):
                success = save_to_google_sheets(
                    file_name=file_name,
                    transcription=transcription
                )
                if success:
                    st.success("Транскрипция сохранена в Google Таблицу.")
                else:
                    st.error("Не удалось сохранить транскрипцию.")

            # Форматирование диалога
            with st.spinner("Форматируем диалог..."):
                formatted_dialogue = format_dialogue(transcription)

            st.subheader("Диалог")
            st.write(formatted_dialogue)

            # Сохранение диалога
            with st.spinner("Сохраняем диалог..."):
                success = save_to_google_sheets(
                    file_name=file_name,
                    dialogue=formatted_dialogue
                )
                if success:
                    st.success("Диалог сохранен в Google Таблицу.")
                else:
                    st.error("Не удалось сохранить диалог.")

            # Критерии оценки
            criteria = """
            1. Установил ли менеджер контакт с клиентом (приветствие, презентация себя исходя из ситуации клиента, обращение по имени). Оценка "1" - да, контакт установил, оценка "0.5" - частично контакт установил, но некоторые пункты упустил, оценка "0" - нет, контакт не был установлен.
            2. Было ли выполнено менеджером программирование на диалог (проговорил структуру диалога, получил согласие от клиента, выяснил откуда узнал о нас клиент, задал вопрос о информации о нас). Оценка "1" - да, выполнил программирование на диалог, оценка "0.5" - частично выполнил программирование на диалог, но некоторые пункты упустил, оценка "0" - нет, программирование на диалог не выполнил.
            3. Задал ли менеджер 2 открытых ситуационных вопроса для выявления потребности клиента. Оценка "1" - да, все вопросы заданы, оценка "0.5" - частично, задан всего один ситуационный вопрос, оценка "0" - нет, вопросы не заданы.
            4. Рассчитана ли сумма долга исходя из ежемесячных платежей, сумма по договору, резюмирована ли полная картина по ситуации клиента, произведен ли расчет по удержаниям доходов, если у клиента уже приставы. Оценка "1" - да, выполнено все перечисленное, оценка "0.5" - частично выполнено перечисленное, но некоторые пункты упущены, оценка "0" - нет, не выполнено.
            5. Был ли представлен и подробно описан кейс №1 с именем клиента, суммой долга и полным описанием ситуации. Оценка "1" - да, кейс представлен, оценка "0.5" - кейс представлен частично, упомянут вкратце или без имени клиента, оценка "0" - нет, кейс не представлен.
            6. Выявил ли менеджер боль клиента с помощью открытых вопросов. Оценка "1" - да, боль выявлена, оценка "0.5" - частично выявлена, оценка "0" - нет, боль не выявлена.
            7. Было ли присоединение, эмпатия, усиление боли через кейс №2. Оценка "1" - да, действия выполнены, оценка "0.5" - частично выполнены, оценка "0" - нет, действия не выполнены.
            8. Нарисовал ли менеджер картинку позитивного и негативного будущего, используя боль клиента. Оценка "1" - да, картина нарисована, оценка "0.5" - частично нарисована, оценка "0" - нет, картина не нарисована.
            9. Была ли подробно описана схема банкротства и эффективно представлен кейс №3, привязанный к боли клиента. Оценка "1" - да, схема и кейс представлены, оценка "0.5" - частично представлены, оценка "0" - нет, не представлены.
            10. Уточнил ли менеджер намерения клиента, задав вопрос "Нравится ли вам идея списать долги?". Оценка "1" - да, вопрос задан, оценка "0" - нет, вопрос не задан.
            11. Попытался ли менеджер закрыть клиента на полный платеж или на рассрочку менее 10 месяцев, задав вопрос “За сколько месяцев справились бы с этой суммой?”. Оценка "1" - да, попытка сделана, оценка "0.5" - частично сделана, оценка "0" - нет, попытка не сделана.
            12. Был ли сделан финальный призыв к действию с использованием оффера/боли/проблемы клиента. Оценка "1" - да, призыв сделан, оценка "0.5" - частично сделан, и что-то упущено из оффера/боли/проблемы клиента, оценка "0" - нет, призыв не сделан.
            13. Упомянул ли менеджер партнерскую программу. Оценка "1" - да, партнерская программа упомянута, оценка "0" - нет, программа не упомянута.
            """

            # Контроль качества
            with st.spinner("Проводим контроль качества..."):
                qc_analysis, scores = quality_control(formatted_dialogue, criteria)

                # Рассчитываем средний балл
                if scores:
                    average_score = sum(scores) / len(scores)
                else:
                    average_score = 0

            st.subheader("Анализ качества")
            st.write(qc_analysis)
            st.write(f"**Средний балл:** {average_score:.2f}")

            # Сохранение оценки звонка и средней оценки
            with st.spinner("Сохраняем оценку звонка..."):
                success = save_to_google_sheets(
                    file_name=file_name,
                    call_evaluation=qc_analysis,
                    average_score=average_score
                )
                if success:
                    st.success("Оценка звонка сохранена в Google Таблицу.")
                else:
                    st.error("Не удалось сохранить оценку звонка.")

            # Определение ошибок
            with st.spinner("Определяем ошибки менеджера..."):
                manager_errors = detect_errors(formatted_dialogue)

            st.subheader("Ошибки менеджера")
            st.write(manager_errors)

            # Сохранение ошибок менеджера
            with st.spinner("Сохраняем ошибки менеджера..."):
                success = save_to_google_sheets(
                    file_name=file_name,
                    manager_errors=manager_errors
                )
                if success:
                    st.success("Ошибки менеджера сохранены в Google Таблицу.")
                else:
                    st.error("Не удалось сохранить ошибки менеджера.")

            # Рекомендации
            with st.spinner("Формируем рекомендации..."):
                manager_recommendations = generate_recommendations(formatted_dialogue)

            st.subheader("Рекомендации для менеджера")
            st.write(manager_recommendations)

            # Сохранение рекомендаций
            with st.spinner("Сохраняем рекомендации..."):
                success = save_to_google_sheets(
                    file_name=file_name,
                    improvement_recommendations=manager_recommendations
                )
                if success:
                    st.success("Рекомендации сохранены в Google Таблицу.")
                else:
                    st.error("Не удалось сохранить рекомендации.")

            # Вопросы клиента
            with st.spinner("Извлекаем вопросы клиента..."):
                client_questions = extract_client_questions(formatted_dialogue)

            st.subheader("Вопросы клиента")
            st.write(client_questions)

            # Сохранение вопросов клиента
            with st.spinner("Сохраняем вопросы клиента..."):
                success = save_to_google_sheets(
                    file_name=file_name,
                    client_questions=client_questions
                )
                if success:
                    st.success("Вопросы клиента сохранены в Google Таблицу.")
                else:
                    st.error("Не удалось сохранить вопросы клиента.")

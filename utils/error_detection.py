# utils/error_detection.py
import openai

def detect_errors(formatted_dialogue):
    error_prompt = f"""
    Действуй как тренер по продажам. Компания занимается банкротством физлиц. Проанализируй диалог и выдели основные ошибки менеджера.

    Диалог:

    \"\"\"{formatted_dialogue}\"\"\"

    Ошибки:
    """

    error_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": error_prompt}
        ],
        temperature=0.7
    )

    manager_errors = error_response['choices'][0]['message']['content']
    return manager_errors

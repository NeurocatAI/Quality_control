# utils/dialogue_formatting.py
import openai

def format_dialogue(transcription):
    dialogue_prompt = f"""
    Следующая транскрипция не содержит распределения реплик между говорящими:
    \"\"\"{transcription}\"\"\"

    Пожалуйста, отформатируйте её как диалог между 'Менеджером' и 'Клиентом', распределив реплики между ними.

    Диалог:
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": dialogue_prompt}
        ],
        temperature=0.7
    )

    formatted_dialogue = response['choices'][0]['message']['content']
    return formatted_dialogue

# utils/client_questions.py
import openai

def extract_client_questions(formatted_dialogue):
    questions_prompt = f"""
    Действуй как аналитик звонков. Компания занимается банкротством физлиц. Из следующего диалога извлеките все вопросы, которые задавал клиент. Перечислите их в виде списка.

    Диалог:
    \"\"\"{formatted_dialogue}\"\"\"

    Вопросы клиента:
    """

    questions_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": questions_prompt}
        ],
        temperature=0.7
    )

    client_questions = questions_response['choices'][0]['message']['content']
    return client_questions

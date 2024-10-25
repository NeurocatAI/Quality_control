# utils/recommendations.py
import openai

def generate_recommendations(formatted_dialogue):
    recommendations_prompt = f"""
    На основе диалога и выявленных ошибок предложите конкретные рекомендации для менеджера, чтобы улучшить его работу:

    Диалог:
    \"\"\"{formatted_dialogue}\"\"\"

    Рекомендации:
    """

    recommendations_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": recommendations_prompt}
        ],
        temperature=0.7
    )

    manager_recommendations = recommendations_response['choices'][0]['message']['content']
    return manager_recommendations

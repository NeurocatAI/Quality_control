# utils/quality_control.py
import openai
import re

def quality_control(formatted_dialogue, criteria):
    qc_prompt = f"""
    Оцени работу менеджера в диалоге по этим критериям:

    {criteria}

    Диалог:
    \"\"\"{formatted_dialogue}\"\"\"

    Пожалуйста, предоставьте короткий анализ и оценку для каждого критерия на основе вариантов оценок, которые прописаны в каждом из критериев.

    И в конце выпиши все получившиеся оценки в переменную score=[], которую я буду использовать в дальнейшем.
    """

    qc_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": qc_prompt}
        ],
        temperature=0.7
    )

    qc_analysis = qc_response['choices'][0]['message']['content']

    # Извлекаем оценки из ответа
    scores = extract_scores(qc_analysis)

    return qc_analysis, scores

def extract_scores(qc_analysis):
    # Используем регулярное выражение для поиска строки с оценками
    match = re.search(r'score\s*=\s*\[(.*?)\]', qc_analysis, re.DOTALL)
    if match:
        scores_str = match.group(1)
        # Разбиваем строку на отдельные оценки и преобразуем в числа
        scores_list = [float(s.strip()) for s in scores_str.split(',')]
        return scores_list
    else:
        return []


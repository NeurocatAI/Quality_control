# utils/quality_control.py
import openai

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
    return qc_analysis

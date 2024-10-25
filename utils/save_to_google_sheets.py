# utils/save_to_google_sheets.py
import requests

def save_to_google_sheets(
    unique_id,
    file_name,
    transcription=None,
    dialogue=None,
    call_evaluation=None,
    average_score=None,
    manager_errors=None,
    improvement_recommendations=None,
    client_questions=None
):
    url = 'https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec'  # Укажите ваш URL скрипта
    data = {
        'unique_id': unique_id,
        'file_name': file_name,
        'transcription': transcription,
        'dialogue': dialogue,
        'call_evaluation': call_evaluation,
        'average_score': average_score,
        'manager_errors': manager_errors,
        'improvement_recommendations': improvement_recommendations,
        'client_questions': client_questions
    }
    try:
        response = requests.post(url, json=data)
        result = response.json()
        return result.get('status') == 'success'
    except Exception as e:
        print(f"Ошибка при сохранении в Google Sheets: {e}")
        return False

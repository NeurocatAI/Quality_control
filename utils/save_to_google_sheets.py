# utils/save_to_google_sheets.py
import requests

def save_to_google_sheets(
    file_name,
    transcription=None,
    dialogue=None,
    call_evaluation=None,
    average_score=None,
    manager_errors=None,
    improvement_recommendations=None,
    client_questions=None
):
    url = 'https://script.google.com/macros/s/AKfycbzCkT2sYTvXhBZL4NAy5Cj-ZhZFMOcc70Hz7eICUTkzY-Q3Bebr196CRSd8AcN-LWc/exec'
    data = {
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

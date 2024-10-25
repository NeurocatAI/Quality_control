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
    client_questions=None,
    row_index=None
):
    url = '1HKvZIO9GrZvte4GpqDEpW-S0dLc5IaKH1CrtKAT6e1A'  
    data = {
        'file_name': file_name,
        'transcription': transcription,
        'dialogue': dialogue,
        'call_evaluation': call_evaluation,
        'average_score': average_score,
        'manager_errors': manager_errors,
        'improvement_recommendations': improvement_recommendations,
        'client_questions': client_questions,
        'row_index': row_index
    }
    try:
        response = requests.post(url, json=data)
        result = response.json()
        # Если вернулся новый row_index, сохраняем его
        if 'row_index' in result:
            return result.get('status') == 'success', result['row_index']
        else:
            return result.get('status') == 'success', row_index
    except Exception as e:
        print(f"Ошибка при сохранении в Google Sheets: {e}")
        return False, row_index

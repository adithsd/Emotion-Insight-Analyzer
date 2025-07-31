from transformers import pipeline

def emotion_detector(text):
    
    emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)
    
    predictions = emotion_classifier(text)[0]

    
    emotion_scores = {emotion['label'].lower(): emotion['score'] for emotion in predictions}

    
    dominant_emotion = max(emotion_scores, key=emotion_scores.get)
    response=dominant_emotion

    return response



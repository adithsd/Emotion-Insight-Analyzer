
from flask import Flask, request, render_template
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from emotion_detection import emotion_detector
from database import db, EmotionLog
from sqlalchemy import func
app = Flask(__name__)

# ✅ Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emotions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # ✅ Initialize DB with Flask app

@app.route("/", methods=["GET", "POST"])
def index():
    emotion = None
    if request.method == "POST":
        user_text = request.form.get("user_text")
        if user_text:
            emotion = emotion_detector(user_text)
            # ✅ Store result in the database
            entry = EmotionLog(input_text=user_text, detected_emotion=emotion)
            db.session.add(entry)
            db.session.commit()
    return render_template("index.html", result=emotion)

@app.route("/logs")
def logs():
    entries = EmotionLog.query.order_by(EmotionLog.timestamp.desc()).all()
    return render_template("logs.html", entries=entries)

@app.route("/dashboard")
def dashboard():
    # Emotion counts for bar chart
    raw_counts = db.session.query(
        EmotionLog.detected_emotion,
        func.count(EmotionLog.detected_emotion)
    ).group_by(EmotionLog.detected_emotion).all()
    emotion_counts = [(row[0], row[1]) for row in raw_counts]

    # Emotion trend over time
    query_result = db.session.query(
        func.strftime('%Y-%m-%d', EmotionLog.timestamp),
        EmotionLog.detected_emotion,
        func.count()
    ).group_by(
        func.strftime('%Y-%m-%d', EmotionLog.timestamp),
        EmotionLog.detected_emotion
    ).all()
    emotion_by_date = [(row[0], row[1], row[2]) for row in query_result]

    # Recent negative feedback
    recent_critical = EmotionLog.query.filter(
        EmotionLog.detected_emotion.in_(['anger', 'sadness', 'fear'])
    ).order_by(EmotionLog.timestamp.desc()).limit(5).all()

    return render_template("dashboard.html",
                           emotion_counts=emotion_counts,
                           emotion_by_date=emotion_by_date,
                           recent_critical=recent_critical)

from flask import request

@app.route("/export")
def export_page():
    emotions = request.args.getlist("emotion")
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    query = EmotionLog.query

    if emotions:
        query = query.filter(EmotionLog.detected_emotion.in_(emotions))
    if start_date:
        query = query.filter(EmotionLog.timestamp >= start_date)
    if end_date:
        query = query.filter(EmotionLog.timestamp <= end_date)

    logs = query.order_by(EmotionLog.timestamp.desc()).limit(50).all()

    # pass current filters to template for persistence
    return render_template("export.html", entries=logs,
                           selected_emotions=emotions,
                           start_date=start_date,
                           end_date=end_date)

@app.route("/download")
def download_csv():
    from io import StringIO
    import csv
    from flask import Response

    emotions = request.args.getlist("emotion")
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    query = EmotionLog.query

    if emotions:
        query = query.filter(EmotionLog.detected_emotion.in_(emotions))
    if start_date:
        query = query.filter(EmotionLog.timestamp >= start_date)
    if end_date:
        query = query.filter(EmotionLog.timestamp <= end_date)

    logs = query.order_by(EmotionLog.timestamp.desc()).all()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Input Text", "Detected Emotion", "Timestamp"])
    for log in logs:
        writer.writerow([log.id, log.input_text, log.detected_emotion, log.timestamp])

    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=filtered_emotion_logs.csv"}
    )

@app.route("/download_xlsx")
def download_xlsx():
    from io import BytesIO
    from flask import send_file
    import openpyxl

    emotions = request.args.getlist("emotion")
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    query = EmotionLog.query
    if emotions:
        query = query.filter(EmotionLog.detected_emotion.in_(emotions))
    if start_date:
        query = query.filter(EmotionLog.timestamp >= start_date)
    if end_date:
        query = query.filter(EmotionLog.timestamp <= end_date)

    logs = query.order_by(EmotionLog.timestamp.desc()).all()

    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Emotion Logs"
    ws.append(["ID", "Input Text", "Detected Emotion", "Timestamp"])

    for log in logs:
        ws.append([log.id, log.input_text, log.detected_emotion, log.timestamp.strftime('%Y-%m-%d %H:%M')])

    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='emotion_logs.xlsx'
    )




if __name__ == "__main__":
    app.run(debug=True)

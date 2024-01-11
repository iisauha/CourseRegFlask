from flask import Flask, render_template, request, redirect
from slc_pandas import *

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/')
def home():
    data = pd.read_csv("ScheduleFull.txt", sep='|')
    fall_data = data[data["Subterm"].isin(['Spring', 'Year'])]
    course_titles = fall_data["CourseTitle"].tolist()
    course_titles = sorted(list(set(course_titles)))
    return render_template('index.html', course_titles=course_titles)

@app.route('/generate_schedule', methods=['GET'])
def generate_schedule():
    courses = request.args.get('courses')
    data_list = str(courses).split('|')
    subterm_conflicts(data_list)
    return redirect('/')

if __name__ == '__main__':
    app.run()
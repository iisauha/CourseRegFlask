#Imports necessary libraries
import pandas as pd
import datetime as datetime
import itertools
import webbrowser
import os

# Read in the schedule text file and convert it into a DataFrame
full_schedule = pd.read_csv("ScheduleFull.txt", sep='|')


def subterm_conflicts(selections):
    global bad
    bad = True
    #Re-initialize the schedule in order to prevent NumPy error
    full_schedule = pd.read_csv("ScheduleFull.txt", sep='|')
    #Extracts courses data frames based off the selections inputted 
    courses =[full_schedule[full_schedule["CourseTitle"] == selection] for selection in selections]
    codes = []
    #For each course data frame, their course title is extracted and appended to codes
    for course in courses:
        if len(course) == 0:
            codes.append(course.CourseTitle.values)
        else:
            codes.append(course.CourseTitle.values[0])
    
    if len(set(codes)) == len(codes):
    #Checks if sub terms of all the semesters fall within the same sub term by keeping count 
        semesters = [course['Subterm'].values[0] for course in courses]
        fall_count = semesters.count('Fall')
        spring_count = semesters.count('Spring')
        year_count = semesters.count('Year')
        fall_count += year_count
        spring_count += year_count
        if spring_count > fall_count:
            weekday_conflicts(*[course[course["Subterm"] == semester] for course, semester in zip(courses, semesters)])  # Spring
        elif fall_count >  spring_count:
            weekday_conflicts(*[course[course["Subterm"] == semester] for course, semester in zip(courses, semesters)])  # Fall
        else:
            print('Check to make sure all courses selected are in the same semester.')
            bad = False
    else:
        print('You selected the same class multiple times.')

def weekday_conflicts(*courses): 
    #Basic data structure for each course [Open, {GC}, {Labs}]
    course_lists = [[], {}, {}]
    courseSchedules = []
    for course in courses:
        core = []
        #extracts defined parameters for each course
        for i in range(len(course)):
            course_title = course['CourseTitle'].values[i]
            course_days = course['CourseDays'].values[i]
            time_slot = course['TimeSlot'].values[i]
            comments = course['Comments'].values[i]

            # Expand multiple days for a single course with multiple days 
            if len(course_days) > 1:
                for i in range(len(course_days)):
                    core.append((course_title, course_days[i], time_slot, comments))
            else:
                core.append((course_title, course_days, time_slot, comments))

            # Separate labs and group conferences from core courses
            # Differentiates comments for each course 
            if 'Lab' in str(comments):
                course_lists[2].setdefault(course_title, []).append((course_title, course_days[0], time_slot, comments))
            elif 'roup' in str(comments):
                course_lists[1].setdefault(course_title, []).append((course_title, course_days[0], time_slot, comments))
            else:
                if len(course_days) > 1:
                    for i in range(len(course_days)):
                        course_lists[0].append((course_title, course_days[i], time_slot, comments))
                else:
                    course_lists[0].append((course_title, course_days, time_slot, comments))
        courseSchedules.append(core)

    # Check for conflicts in the core seminar or lectures
    check, conflicts = check_overlap(course_lists[0])

    #Uses boolean value to check if conflict found in core classes
    if check:
        # Handle conflicts and generate HTML for display
        singleConflicts = [item for pair in conflicts for item in pair]
        final_class_html = toPandasConf(singleConflicts)
        pandyList = [toPandasPos(pos, num) for num, pos in enumerate(courseSchedules)]

        # Create HTML file with the conflict listing
        catalog_link = 'https://www.sarahlawrence.edu/undergraduate/2023-2024-catalogue.pdf'
        hyperlink_html = f'<p style="font-size: 18px;"><a href="{catalog_link}" style="color: #3366BB; text-decoration: none; font-weight: bold;">Sarah Lawrence College Course Catalog</a></p>'
        note_html = '<p><center><strong style="font-size: 24px;">Conflict found in the core class times:</strong></center></p>\n'
        css_link = '<link rel="stylesheet" href="stylingtable.css">\n'
        course_note_html = '<p><center><strong style="font-size: 24px;">Courses Selected:</strong></center></p>\n'

        script_dir = os.path.dirname(os.path.abspath(__file__))
        relative_path = "templates"
        html_file_name = "final_class.html"
        html_file_path = os.path.join(script_dir, relative_path, html_file_name)


        #Writes pandas data frame and styling to 'final_class.html'
        with open(html_file_path, "w") as file:
            file.write(css_link)
            file.write(note_html)
            file.write(final_class_html)
            file.write(course_note_html)
            for i in pandyList:
                file.write(i)
            file.write(hyperlink_html)

        webbrowser.open(f"file://{html_file_path}")

        
    else:
        # Handle cases with no core conflicts
        schedule_options = []
        all_lists = [course_lists[1][j] for j in course_lists[1]] + [course_lists[2][e] for e in course_lists[2]]
        permutations = list(itertools.product(*all_lists))

        # Generate all possible schedules and check for conflicts
        for perm in permutations:
            class_options = course_lists[0].copy()
            class_options.extend(perm)
            schedule_options.append(class_options)

        conflict_list = []
        possible_list = []
        #Checks if all combinations conflict with core classes
        for option in schedule_options:
            check, conflicts = check_overlap(option)
            if check:
                conflict_list.append(conflicts)
            else:
                possible_list.append(option)

        #Uses boolean logic to check if there are valid schedules 
        if possible_list:
            #Creates a list of html tables for each valid schedule
            pandyList = [toPandasPos(pos, num) for num, pos in enumerate(possible_list)]

            #HTML styling
            catalog_link = 'https://www.sarahlawrence.edu/undergraduate/2023-2024-catalogue.pdf'
            hyperlink_html = f'<p style="font-size: 18px;"><a href="{catalog_link}" style="color: #3366BB; text-decoration: none; font-weight: bold;">Sarah Lawrence College Course Catalog</a></p>'
            note_html = '<p><strong style="font-size: 24px; color: green;">Valid Schedules:</strong></p>\n'
            css_link = '<link rel="stylesheet" href="stylingtable.css">\n'
            table_separator = '<div style="height: 20px;"></div>\n'

            #Root\Base\
            script_dir = os.path.dirname(os.path.abspath(__file__))
            #Relative
            relative_path = "templates" 
            #Filename
            html_file_name = "final_class.html"
            #Root\Base\Relative\Filename
            html_file_path = os.path.join(script_dir, relative_path, html_file_name)

            #Writes pandas data frame and styling to final_class.html
            with open(html_file_path, "w") as file:
                file.write(css_link)
                file.write(note_html)
                for i in pandyList:
                    file.write(i)
                    file.write(table_separator)
                file.write(hyperlink_html)
            
            # Open the HTML file in Default Search Engine
            webbrowser.open(f"file://{html_file_path}")

            return
        else:
            # Handle cases with conflicts in possible schedules
            singleConflicts = [item for pair in conflict_list for item in pair]
            conflictList = []
            for i in singleConflicts:
                first, second = i
                conflictList.append(first)
                conflictList.append(second)
            singleConflicts = [i for n, i in enumerate(conflictList) if i not in conflictList[:n]]
            finalConflicts = non_conf_check(singleConflicts)
            conflicts_html = toPandasConf(finalConflicts)
            pandyList = [toPandasPos(pos, num) for num, pos in enumerate(courseSchedules)]

            #HTML Styling
            catalog_link = 'https://www.sarahlawrence.edu/undergraduate/2023-2024-catalogue.pdf'
            hyperlink_html = f'<p style="font-size: 18px;"><a href="{catalog_link}" style="color: #3366BB; text-decoration: none; font-weight: bold;">Sarah Lawrence College Course Catalog</a></p>'
            conflict_note_html = '<p><center><strong style="font-size: 24px;">Conflict Listing:</strong></center></p>\n'
            css_link = '<link rel="stylesheet" href="stylingtable.css">\n'
            course_note_html = '<p><center><strong style="font-size: 24px;">Courses Selected:</strong></center></p>\n'

            script_dir = os.path.dirname(os.path.abspath(__file__))
            relative_path = "templates"
            html_file_name = "final_class.html"
            html_file_path = os.path.join(script_dir, relative_path, html_file_name)

            with open(html_file_path, "w") as file:
                file.write(css_link)
                file.write(conflict_note_html)
                file.write(conflicts_html)
                file.write(course_note_html)
                for i in pandyList:
                    file.write(i)
                file.write(hyperlink_html)

            webbrowser.open(f"file://{html_file_path}")


def check_overlap(classes):
    # Check for overlapping time slots in courses and return conflicts as tuples.
    conflict = False
    conflict_list = []
    for i in range(len(classes)):
        title, day, time, com = classes[i]
        for j in range(i + 1, len(classes)):
            title_j, day_j, time_j, _ = classes[j]
            if day == day_j and is_time_overlap(time, time_j) and (title_j, _) != (title, com):
                if ((title, day, time, com), (title_j, day_j, time_j, _)) not in conflict_list:
                    conflict_list.append(((title, day, time, com), (title_j, day_j, time_j, _)))
                    conflict = True
                else:
                    conflict = False
    #Returns a boolean and the conflict list
    return conflict, conflict_list

def is_time_overlap(time1, time2):
    # Compare two time slots and check if they overlap.
    start1, end1 = parse_time_slot(time1)
    start2, end2 = parse_time_slot(time2)
    return start1 < end2 and start2 < end1

def parse_time_slot(time_slot):
    # Parse time slots into start and end times.
    start_time, end_time = time_slot.split("-")
    start = datetime.datetime.strptime(start_time.strip(), "%I:%M %p")
    end = datetime.datetime.strptime(end_time.strip(), "%I:%M %p")
    return start, end

def toPandasPos(possible, num):
    # Convert possible schedules to HTML tables using Pandas styling.
    possible_df = pd.DataFrame(possible, columns=['Course Title', 'Day', 'Time', 'Comments'])

    # Time Sorting
    possible_df["Time_Sort"] = possible_df["Time"].apply(parse_time_slot)
    df_sorted = possible_df.sort_values(by="Time_Sort")
    df_sorted.drop("Time_Sort", axis=1, inplace=True)

    # Day sorting
    custom_day_order = ['M', 'T', 'W', 'R', 'F']
    df_sorted['Day'] = pd.Categorical(df_sorted['Day'], categories=custom_day_order, ordered=True)
    df_sorted = df_sorted.sort_values('Day')
    final_class_html = df_sorted.to_html(index=False)
    styled_df = df_sorted.style.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#00843D'), ('color', 'white'), ('text-align', 'center')]},
        {'selector': 'td', 'props': [('text-align', 'center'), ('background-color', '#E0E0E0')]},
        {'selector': 'tr:hover', 'props': [('background-color', '#FFFF99')]}])

    final_class_html = styled_df.hide(axis='index').render()
    return final_class_html

def toPandasConf(conflicts):
    # Convert conflicts to HTML tables using Pandas styling.

    # Time sorting
    final_class_list_df = pd.DataFrame(conflicts, columns=['Course Title', 'Day', 'Time', 'Comments'])
    final_class_list_df["Time_Sort"] = final_class_list_df["Time"].apply(parse_time_slot)
    df_sorted = final_class_list_df.sort_values(by="Time_Sort")
    df_sorted.drop("Time_Sort", axis=1, inplace=True)

    #Day Sorting
    custom_day_order = ['M', 'T', 'W', 'R', 'F']
    df_sorted['Day'] = pd.Categorical(df_sorted['Day'], categories=custom_day_order, ordered=True)
    df_sorted = df_sorted.sort_values('Day')
    day_time_list = list(df_sorted[['Day', 'Time']].apply(tuple, axis=1))
    final_len = get_chuck_sizes(day_time_list)
    styler = highlightStyle(final_len, df_sorted)

    final_class_html = styler.hide(axis='index').render()
    return final_class_html

def non_conf_check(singleConflicts):
    # Remove duplicate conflicts from the conflict set.
    conflict_set = {}
    for i in range(0, len(singleConflicts), 2):
        if i + 1 == len(singleConflicts):
            pass
        else:
            list1, list2 = singleConflicts[i], singleConflicts[i + 1]
            title1i, _, _, com1i = list1
            title2i, _, _, com2i = list2
            if ((title1i, com1i), (title2i, com2i)) not in conflict_set:
                conflict_set[((title1i, com1i), (title2i, com2i))] = []
                conflict_set[((title1i, com1i), (title2i, com2i))].append(i)
                conflict_set[((title1i, com1i), (title2i, com2i))].append(i + 1)
            else:
                conflict_set[((title1i, com1i), (title2i, com2i))].append(i)
                conflict_set[((title1i, com1i), (title2i, com2i))].append(i + 1)
    for i in conflict_set.values():
        if len(i) > 2:
            for j in range(len(i)):
                singleConflicts.pop(i[j] - j)
    return singleConflicts

def highlightStyle(grouping, df_sorted):
    # Highlight the conflicting courses with different colors using Pandas styling.
    color_list = ['#ffba08', '#f48c06', '#e85d04', '#dc2f02', '#ba2929', '#9d0208']
    start_idx = 0
    styler = df_sorted.style
    all_row_styles = []

    for i in range(len(grouping)):
        chunk_size = grouping[i]
        chunk_indices = range(start_idx, start_idx + chunk_size)
        chunk_color = color_list[i]

        row_styles = []
        for row_idx in chunk_indices:
            row_style = {'selector': f'tr:nth-child({row_idx + 1})', 'props': f'background-color: {chunk_color}'}
            row_styles.append(row_style)

        all_row_styles.extend(row_styles)
        start_idx += chunk_size

    header_style = {'selector': 'th', 'props': [('background-color', '#36454F'), ('color', 'white'), ('text-align', 'center')]}
    all_row_styles.append(header_style)

    styler = styler.set_table_styles(all_row_styles, overwrite=False)
    return styler

def get_chuck_sizes(day_time_list):
    # Calculate the sizes of chunks for highlighting conflicting courses.
    final_len = []
    counter = 0
    for i in range(1, len(day_time_list)):
        day, time = day_time_list[i - 1]
        day1, time1 = day_time_list[i]
        if day1 == day and is_time_overlap(time, time1):
            if counter >= 2:
                counter += 1
            else:
                counter += 2
        else:
            final_len.append(counter)
            counter = 0
        if i == len(day_time_list) - 1:
            final_len.append(counter)
    return final_len

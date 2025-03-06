"""Script to assign different station and year-month values for each student."""
import random
import pandas as pd


def assign_random_combinations(students, stations, year_months):
    """
    Assign random main and backup (station, year-month) pairs to each student.

    :param students: list of student names
    :param stations: list of station names
    :param year_months: list of year-month strings
    :return: pandas DataFrame with columns:
             [Student, Main_Station, Main_YearMonth, Backup_Station, Backup_YearMonth]
    """

    # Total combos needed: 2 combos for each student (main + backup)
    total_needed = len(students) * 2

    # All possible (station, year_month) combos
    possible_combos = [(station, ym) for station in stations for ym in year_months]

    # Make sure we have enough unique combos to assign
    if len(possible_combos) < total_needed:
        raise ValueError("Not enough station-year_month combinations for all students!")

    # Shuffle all combinations in-place
    random.shuffle(possible_combos)

    # Pick exactly as many as we need
    chosen_combos = possible_combos[:total_needed]

    # First half are the main combos, second half are the backups
    main_combos = chosen_combos[:len(students)]
    backup_combos = chosen_combos[len(students):]

    # Build the output data
    data = []
    for i, student_name in enumerate(students):
        data.append({
            "Student": student_name,
            "Main_Station": main_combos[i][0],
            "Main_YearMonth": main_combos[i][1],
            "Backup_Station": backup_combos[i][0],
            "Backup_YearMonth": backup_combos[i][1],
        })

    # Convert to a DataFrame
    df = pd.DataFrame(data)
    return df


if __name__ == '__main__':

    # Example usage
    list_of_stations = ['Kassari', 'Laimjala', 'Pakri', 'Haapsalu', 'Lääne-Nigula', 'Koodu', 'Kuusiku', 'Türi',
                        'Viljandi', 'Väike-Maarja', 'Jõgeva', 'Tartu-Tõravere', 'Otepää', 'Piigaste', 'Valga', 'Võru',
                        'Tuulemäe', 'Tudu', 'Tiirikoja', 'Jõhvi', 'Narva']
    list_of_student = ['Yandar Alekseev', 'Mayin-jesu Ehinlaiye', 'Karina Filippova', 'Gustav Glaase',
                       'Amanda Karakai', 'Helene Armilde Kudre', 'Iris Kuhi', 'Lola Link', 'Reet Männik',
                       'Hannah Mikenberg', 'Ingrette Pärnamägi', 'Kristjan Georg Ristmäe', 'Siim Roov',
                       'Alice Saluorg', 'Elizabeth Šanin', 'Ilja Stetski', 'Kettreen Vinkel']
    list_of_year_months = ['11.23', '12.23', '1.24', '2.24', '3.24', '4.24', '5.24', '6.24', '7.24', '8.24',
                           '9.24', '10.24', '11.24', '12.24', '1.25', '2.25']

    assignments_df = assign_random_combinations(students=list_of_student,
                                                stations=list_of_stations,
                                                year_months=list_of_year_months)
    assignments_df.to_csv('assignments_2025.csv')
"""Assign homework combinations for atmosphere (HW1) and radar (HW2)."""
import random
import pandas as pd


def assign_hw2_combinations(students, stations, years):
    """
    Assign random main and backup (station, year) pairs to each student.

    :param students: list of student names
    :param stations: list of station names
    :param years: list of year strings
    :return: pandas DataFrame with columns:
             [Student, Main_Station, Main_Year, Backup_Station, Backup_Year]
    """

    # Total combos needed: 2 combos for each student (main + backup)
    total_needed = len(students) * 2

    # All possible (station, year) combos
    possible_combos = [(station, year) for station in stations for year in years]

    # Make sure we have enough unique combos to assign
    if len(possible_combos) < total_needed:
        raise ValueError("Not enough station-year combinations for all students!")

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
            "Main_Year": main_combos[i][1],
            "Backup_Station": backup_combos[i][0],
            "Backup_Year": backup_combos[i][1],
        })

    # Convert to a DataFrame
    df = pd.DataFrame(data)
    return df


def assign_hw1_combinations(students, variables, years):
    """
    Assign one random year and two random variables to each student.

    :param students: list of student names
    :param variables: list of variable names
    :param years: list of year strings
    :return: pandas DataFrame with columns:
             [Student, Year, Variable_1, Variable_2]
    """
    if len(variables) < 2:
        raise ValueError("At least two variables are required for HW1 assignments.")

    data = []
    for student_name in students:
        chosen_year = random.choice(years)
        var_1, var_2 = random.sample(variables, 2)
        data.append({
            "Student": student_name,
            "Year": chosen_year,
            "VAR1": var_1,
            "VAR2": var_2,
        })

    return pd.DataFrame(data)


if __name__ == '__main__':

    # Example usage
    list_of_student = ['Yandar Alekseev', 'Iiris Aljes', 'Arina Gotsenko', 'Hele-Riin Hallik',
                   'Claudia-Isabel Huuse', 'Trinity Jõgisalu', 'Lisette Johanson', 
                   'Katarina Kaleininkas', 'Rene Kaur', 'Kaia Korman', 'Nikita Lagutkin', 
                   'Margot Leheroo', 'Helena Heliise Mardi', 'Regina Poom', 'Avely-Agnes Pumalainen', 
                   'Elisa Rajas', 'Kristjan Georg Ristmäe', 'Liis Seenemaa', 'Jaan Eerik Sorga',
                   'Grete Anette Treiman', 'Taavi Tunis', 'Heily Untera']

    list_of_years = ['2020', '2021', '2022', '2023', '2024', '2025']

    hw1_variables = ['NO2', 'O3', 'CH4', 'CO']
    
    hw2_stations = ['Kihnu', 'Pärnu', 'Kuusiku', 'Türi', 'Tooma', 'Jõgeva', 'Tiirikoja', 'Tartu-Tõravere',
                    'Viljandi', 'Valga', 'Võru']

    
    hw1_assignments_df = assign_hw1_combinations(students=list_of_student,
                                                 variables=hw1_variables,
                                                 years=list_of_years)
    hw1_assignments_df.to_csv('hw1_assignments_2026.csv', index=False)

    hw2_assignments_df = assign_hw2_combinations(students=list_of_student,
                                                 stations=hw2_stations,
                                                 years=list_of_years)
    hw2_assignments_df.to_csv('hw2_assignments_2026.csv', index=False)

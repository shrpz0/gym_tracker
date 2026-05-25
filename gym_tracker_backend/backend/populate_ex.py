import requests

API_URL = "http://127.0.0.1:8000/api/tracker/Exercise/"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc5MzEzMzI5LCJpYXQiOjE3NzkzMTMwMjksImp0aSI6IjBiNTE4NGY4ZDMxNTRhOGY5ZjgxYzNjMTQxNTBjZDU3IiwidXNlcl9pZCI6Mn0.2hNtf2woxsVlWmOW8EzlWgbcfqT5eiRYBgTHsYQXk5s"

EXERCISES = [
    ("Barbell Bench Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Dumbbell Bench Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Incline Bench Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Incline DB Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Decline Bench Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Close Grip Bench Press","TRICEPS",[11,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Paused Bench Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Smith Bench Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Machine Chest Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Seated Chest Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Push Up","CHEST",[14,15,16],"HORIZONTAL_PUSH","UPPER",True),
    ("Weighted Push Up","CHEST",[14,15,16],"HORIZONTAL_PUSH","UPPER",True),
    ("Deficit Push Up","CHEST",[14,15,16],"HORIZONTAL_PUSH","UPPER",True),
    ("Incline Push Up","CHEST",[14,15,16],"HORIZONTAL_PUSH","UPPER",True),
    ("Decline Push Up","CHEST",[14,15,16],"HORIZONTAL_PUSH","UPPER",True),
    ("Dips","TRICEPS",[11,15],"VERTICAL_PUSH","UPPER",True),
    ("Chest Dips","CHEST",[14,15],"VERTICAL_PUSH","UPPER",True),
    ("Assisted Dips","TRICEPS",[11,15],"VERTICAL_PUSH","UPPER",True),
    ("Cable Chest Fly","CHEST",[],"OTHER","UPPER",False),
    ("Pec Deck Fly","CHEST",[],"OTHER","UPPER",False),
    ("DB Chest Fly","CHEST",[],"OTHER","UPPER",False),
    ("Incline DB Fly","CHEST",[15],"OTHER","UPPER",False),
    ("Low Cable Fly","CHEST",[15],"OTHER","UPPER",False),
    ("High Cable Fly","CHEST",[],"OTHER","UPPER",False),
    ("Svend Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",False),

    ("Overhead Press","SHOULDERS",[14,16],"VERTICAL_PUSH","UPPER",True),
    ("Seated Overhead Press","SHOULDERS",[14],"VERTICAL_PUSH","UPPER",True),
    ("DB Shoulder Press","SHOULDERS",[14],"VERTICAL_PUSH","UPPER",True),
    ("Arnold Press","SHOULDERS",[14],"VERTICAL_PUSH","UPPER",True),
    ("Smith Shoulder Press","SHOULDERS",[14],"VERTICAL_PUSH","UPPER",True),
    ("Machine Shoulder Press","SHOULDERS",[14],"VERTICAL_PUSH","UPPER",True),
    ("Push Press","SHOULDERS",[14,17,19,16],"VERTICAL_PUSH","FULL",True),
    ("Landmine Press","SHOULDERS",[11,14,16],"VERTICAL_PUSH","UPPER",True),
    ("Half Kneeling Landmine Press","SHOULDERS",[11,14,16],"VERTICAL_PUSH","UPPER",True),
    ("Pike Push Up","SHOULDERS",[14,16],"VERTICAL_PUSH","UPPER",True),
    ("Handstand Push Up","SHOULDERS",[14,16],"VERTICAL_PUSH","UPPER",True),
    ("Lateral Raise","SHOULDERS",[],"OTHER","UPPER",False),
    ("Cable Lateral Raise","SHOULDERS",[],"OTHER","UPPER",False),
    ("Machine Lateral Raise","SHOULDERS",[],"OTHER","UPPER",False),
    ("Front Raise","SHOULDERS",[],"OTHER","UPPER",False),
    ("Cable Front Raise","SHOULDERS",[],"OTHER","UPPER",False),
    ("Rear Delt Fly","SHOULDERS",[12],"HORIZONTAL_PULL","UPPER",False),
    ("Reverse Pec Deck","SHOULDERS",[12],"HORIZONTAL_PULL","UPPER",False),
    ("Face Pull","SHOULDERS",[12,13],"HORIZONTAL_PULL","UPPER",False),
    ("Upright Row","SHOULDERS",[12,13],"VERTICAL_PULL","UPPER",True),
    ("Barbell Shrug","NECK",[15,22],"OTHER","UPPER",False),
    ("DB Shrug","NECK",[15,22],"OTHER","UPPER",False),
    ("Cable Shrug","NECK",[15,22],"OTHER","UPPER",False),

    ("Skull Crusher","TRICEPS",[],"OTHER","UPPER",False),
    ("Cable Triceps Pushdown","TRICEPS",[],"OTHER","UPPER",False),
    ("Rope Pushdown","TRICEPS",[],"OTHER","UPPER",False),
    ("Overhead Triceps Ext","TRICEPS",[],"OTHER","UPPER",False),
    ("DB Triceps Extension","TRICEPS",[],"OTHER","UPPER",False),
    ("Cable Overhead Extension","TRICEPS",[],"OTHER","UPPER",False),
    ("Bench Dip","TRICEPS",[11,15],"VERTICAL_PUSH","UPPER",True),
    ("Diamond Push Up","TRICEPS",[11,15,16],"HORIZONTAL_PUSH","UPPER",True),
    ("JM Press","TRICEPS",[11,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Tate Press","TRICEPS",[11],"OTHER","UPPER",False),

    ("Pull Up","BACK",[13,15,22,16],"VERTICAL_PULL","UPPER",True),
    ("Chin Up","BACK",[13,22,16],"VERTICAL_PULL","UPPER",True),
    ("Neutral Grip Pull Up","BACK",[13,22,16],"VERTICAL_PULL","UPPER",True),
    ("Wide Grip Pull Up","BACK",[13,15,16],"VERTICAL_PULL","UPPER",True),
    ("Assisted Pull Up","BACK",[13,15],"VERTICAL_PULL","UPPER",True),
    ("Lat Pulldown","BACK",[13,22],"VERTICAL_PULL","UPPER",True),
    ("Wide Lat Pulldown","BACK",[13,22],"VERTICAL_PULL","UPPER",True),
    ("Close Grip Pulldown","BACK",[13,22],"VERTICAL_PULL","UPPER",True),
    ("Straight Arm Pulldown","BACK",[14],"VERTICAL_PULL","UPPER",False),
    ("Barbell Row","BACK",[13,18,19,16,22],"HORIZONTAL_PULL","UPPER",True),
    ("Pendlay Row","BACK",[13,18,19,16,22],"HORIZONTAL_PULL","UPPER",True),
    ("DB Row","BACK",[13,22,16],"HORIZONTAL_PULL","UPPER",True),
    ("Chest Supported Row","BACK",[13,22],"HORIZONTAL_PULL","UPPER",True),
    ("Seated Cable Row","BACK",[13,22],"HORIZONTAL_PULL","UPPER",True),
    ("Machine Row","BACK",[13,22],"HORIZONTAL_PULL","UPPER",True),
    ("T Bar Row","BACK",[13,22,16],"HORIZONTAL_PULL","UPPER",True),
    ("Meadows Row","BACK",[13,22,16],"HORIZONTAL_PULL","UPPER",True),
    ("Inverted Row","BACK",[13,16,22],"HORIZONTAL_PULL","UPPER",True),
    ("Seal Row","BACK",[13,22],"HORIZONTAL_PULL","UPPER",True),
    ("Rack Pull","BACK",[18,19,22],"HINGE","FULL",True),
    ("Deadlift","BACK",[18,19,17,16,22],"HINGE","FULL",True),
    ("Sumo Deadlift","GLUTES",[18,17,12,16,22],"HINGE","FULL",True),
    ("Romanian Deadlift","HAMSTRINGS",[19,12,22],"HINGE","LOWER",True),
    ("DB Romanian Deadlift","HAMSTRINGS",[19,12,22],"HINGE","LOWER",True),
    ("Good Morning","HAMSTRINGS",[19,12,16],"HINGE","LOWER",True),
    ("Back Extension","HAMSTRINGS",[19,12],"HINGE","LOWER",True),
    ("Hip Extension Machine","GLUTES",[18],"HINGE","LOWER",False),

    ("Preacher Curl","BICEPS",[],"OTHER","UPPER",False),
    ("Barbell Curl","BICEPS",[22],"OTHER","UPPER",False),
    ("DB Curl","BICEPS",[22],"OTHER","UPPER",False),
    ("Incline DB Curl","BICEPS",[22],"OTHER","UPPER",False),
    ("Hammer Curl","BICEPS",[22],"OTHER","UPPER",False),
    ("Cable Curl","BICEPS",[22],"OTHER","UPPER",False),
    ("EZ Bar Curl","BICEPS",[22],"OTHER","UPPER",False),
    ("Concentration Curl","BICEPS",[22],"OTHER","UPPER",False),
    ("Spider Curl","BICEPS",[22],"OTHER","UPPER",False),
    ("Reverse Curl","FOREARMS",[13],"OTHER","UPPER",False),
    ("Wrist Curl","FOREARMS",[],"OTHER","UPPER",False),
    ("Reverse Wrist Curl","FOREARMS",[],"OTHER","UPPER",False),

    ("Back Squat","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("High Bar Squat","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("Low Bar Squat","GLUTES",[17,18,16],"SQUAT","LOWER",True),
    ("Front Squat","QUADS",[19,16,12],"SQUAT","LOWER",True),
    ("Goblet Squat","QUADS",[19,16],"SQUAT","LOWER",True),
    ("Box Squat","GLUTES",[17,18,16],"SQUAT","LOWER",True),
    ("Pause Squat","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("Hack Squat","QUADS",[19],"SQUAT","LOWER",True),
    ("Machine Hack Squat","QUADS",[19],"SQUAT","LOWER",True),
    ("Smith Squat","QUADS",[19,18],"SQUAT","LOWER",True),
    ("Leg Press","QUADS",[19,18],"SQUAT","LOWER",True),
    ("Single Leg Press","QUADS",[19,18],"SQUAT","LOWER",True),
    ("Bulgarian Split Squat","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("DB Split Squat","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("Walking Lunge","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("Reverse Lunge","GLUTES",[17,18,16],"SQUAT","LOWER",True),
    ("Forward Lunge","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("Lateral Lunge","GLUTES",[17,18,16],"SQUAT","LOWER",True),
    ("Step Up","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("Pistol Squat","QUADS",[19,18,16],"SQUAT","LOWER",True),
    ("Sissy Squat","QUADS",[],"SQUAT","LOWER",False),
    ("Leg Extension","QUADS",[],"OTHER","LOWER",False),
    ("Seated Leg Curl","HAMSTRINGS",[],"OTHER","LOWER",False),
    ("Lying Leg Curl","HAMSTRINGS",[],"OTHER","LOWER",False),
    ("Standing Leg Curl","HAMSTRINGS",[],"OTHER","LOWER",False),
    ("Nordic Curl","HAMSTRINGS",[19,20],"HINGE","LOWER",False),
    ("Glute Ham Raise","HAMSTRINGS",[19,20],"HINGE","LOWER",True),
    ("Hip Thrust","GLUTES",[18,17,16],"HINGE","LOWER",True),
    ("Barbell Hip Thrust","GLUTES",[18,17,16],"HINGE","LOWER",True),
    ("Single Leg Hip Thrust","GLUTES",[18,17,16],"HINGE","LOWER",True),
    ("Glute Bridge","GLUTES",[18,16],"HINGE","LOWER",True),
    ("Cable Pull Through","GLUTES",[18,16],"HINGE","LOWER",False),
    ("Kettlebell Swing","GLUTES",[18,12,16],"HINGE","FULL",True),
    ("Trap Bar Deadlift","QUADS",[19,18,12,16,22],"HINGE","FULL",True),
    ("Stiff Leg Deadlift","HAMSTRINGS",[19,12,22],"HINGE","LOWER",True),
    ("Single Leg RDL","HAMSTRINGS",[19,16],"HINGE","LOWER",True),
    ("Standing Calf Raise","CALVES",[],"OTHER","LOWER",False),
    ("Seated Calf Raise","CALVES",[],"OTHER","LOWER",False),
    ("Leg Press Calf Raise","CALVES",[],"OTHER","LOWER",False),
    ("Donkey Calf Raise","CALVES",[],"OTHER","LOWER",False),
    ("Tibialis Raise","CALVES",[],"OTHER","LOWER",False),
    ("Hip Abduction Machine","GLUTES",[],"OTHER","LOWER",False),
    ("Hip Adduction Machine","GLUTES",[],"OTHER","LOWER",False),
    ("Cable Kickback","GLUTES",[18],"HINGE","LOWER",False),
    ("Frog Pump","GLUTES",[18],"HINGE","LOWER",False),

    ("Plank","CORE",[15,19],"CORE","FULL",False),
    ("Side Plank","CORE",[15,19],"CORE","FULL",False),
    ("Dead Bug","CORE",[],"CORE","FULL",False),
    ("Hollow Body Hold","CORE",[],"CORE","FULL",False),
    ("Crunch","CORE",[],"CORE","UPPER",False),
    ("Cable Crunch","CORE",[],"CORE","UPPER",False),
    ("Reverse Crunch","CORE",[],"CORE","LOWER",False),
    ("Hanging Leg Raise","CORE",[22],"CORE","UPPER",False),
    ("Captain Chair Leg Raise","CORE",[],"CORE","UPPER",False),
    ("Ab Wheel Rollout","CORE",[15,12],"CORE","FULL",True),
    ("Russian Twist","CORE",[],"CORE","UPPER",False),
    ("Pallof Press","CORE",[15],"CORE","UPPER",False),
    ("Wood Chop","CORE",[15],"CORE","FULL",False),
    ("Cable Rotation","CORE",[15],"CORE","UPPER",False),
    ("Mountain Climber","CORE",[15,17],"CORE","FULL",True),
    ("Bird Dog","CORE",[19,12],"CORE","FULL",False),

    ("Farmer Carry","FOREARMS",[12,16,21,20],"CARRY","FULL",True),
    ("Suitcase Carry","CORE",[22,12,21],"CARRY","FULL",True),
    ("Overhead Carry","SHOULDERS",[14,16,22],"CARRY","FULL",True),
    ("Front Rack Carry","CORE",[17,12,22],"CARRY","FULL",True),
    ("Yoke Carry","QUADS",[19,12,16,20],"CARRY","FULL",True),
    ("Sled Push","QUADS",[19,20,16],"SQUAT","LOWER",True),
    ("Sled Pull","HAMSTRINGS",[19,20,16],"HINGE","LOWER",True),

    ("Clean","GLUTES",[18,17,12,15,16,22],"HINGE","FULL",True),
    ("Power Clean","GLUTES",[18,17,12,15,16,22],"HINGE","FULL",True),
    ("Hang Clean","GLUTES",[18,17,12,15,16,22],"HINGE","FULL",True),
    ("Clean and Press","SHOULDERS",[17,19,18,14,12,16],"VERTICAL_PUSH","FULL",True),
    ("Thruster","QUADS",[19,15,14,16],"SQUAT","FULL",True),
    ("Wall Ball","QUADS",[19,15,14,16],"SQUAT","FULL",True),
    ("Snatch","GLUTES",[18,17,12,15,16,22],"HINGE","FULL",True),
    ("Power Snatch","GLUTES",[18,17,12,15,16,22],"HINGE","FULL",True),
    ("Turkish Get Up","SHOULDERS",[16,19,17,14],"OTHER","FULL",True),
    ("Burpee","CORE",[11,14,15,17,19],"OTHER","FULL",True),
    ("Battle Ropes","SHOULDERS",[13,14,16],"OTHER","UPPER",True),
    ("Medicine Ball Slam","CORE",[15,12,14],"HINGE","FULL",True),
    ("Box Jump","QUADS",[19,18,20],"SQUAT","LOWER",True),
    ("Jump Squat","QUADS",[19,18,20],"SQUAT","LOWER",True),
    ("Broad Jump","GLUTES",[17,18,20],"HINGE","LOWER",True),
    ("Rowing Machine","BACK",[17,18,19,13,16],"HORIZONTAL_PULL","FULL",True),
    ("Assault Bike","QUADS",[19,18,20,15],"OTHER","FULL",True),
    ("Rope Climb","BACK",[13,22,16],"VERTICAL_PULL","FULL",True),

    ("Cable Row Single Arm","BACK",[13,22,16],"HORIZONTAL_PULL","UPPER",True),
    ("Machine Pullover","BACK",[11,14],"VERTICAL_PULL","UPPER",False),
    ("DB Pullover","BACK",[11,14,16],"VERTICAL_PULL","UPPER",False),
    ("Scapular Pull Up","BACK",[15],"VERTICAL_PULL","UPPER",False),
    ("Scapular Push Up","CHEST",[15,14],"HORIZONTAL_PUSH","UPPER",False),
    ("Cuban Press","SHOULDERS",[14,12],"VERTICAL_PUSH","UPPER",False),
    ("Z Press","SHOULDERS",[14,16],"VERTICAL_PUSH","UPPER",True),
    ("Bradford Press","SHOULDERS",[14],"VERTICAL_PUSH","UPPER",True),
    ("Pin Press","TRICEPS",[11,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Floor Press","TRICEPS",[11,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Incline Machine Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Decline Machine Press","CHEST",[14,15],"HORIZONTAL_PUSH","UPPER",True),
    ("Cable Crossover","CHEST",[],"OTHER","UPPER",False),
    ("Around The World","CHEST",[15],"OTHER","UPPER",False),
    ("Landmine Squat","QUADS",[19,16],"SQUAT","LOWER",True),
    ("Zercher Squat","QUADS",[19,18,16,12],"SQUAT","FULL",True),
    ("Cossack Squat","GLUTES",[17,18,16],"SQUAT","LOWER",True),
]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

for name, primary, secondary_ids, pattern, region, compound in EXERCISES:
    payload = {
        "name": name,
        "primary_muscle": primary,
        "secondary_muscles_ids": secondary_ids,
        "pattern": pattern,
        "region": region,
        "is_compound": compound,
    }

    response = requests.post(API_URL, json=payload, headers=headers)

    if response.status_code in (200, 201):
        print(f"CREATED: {name}")
        continue

    print(f"\nFAILED: {name}")
    print("STATUS:", response.status_code)

    try:
        error_data = response.json()
        print("ERROR JSON:", error_data)

        # skip duplicates if some were already created
        if response.status_code == 400 and "name" in error_data:
            print(f"SKIPPED DUPLICATE: {name}")
            continue

    except Exception:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("title")
        h1 = soup.find("h1")
        pre = soup.find("pre", {"class": "exception_value"})

        print("DJANGO ERROR TITLE:", title.get_text(strip=True) if title else None)
        print("DJANGO H1:", h1.get_text(strip=True) if h1 else None)
        print("EXCEPTION:", pre.get_text(strip=True) if pre else None)

        print("\nRAW FIRST 3000 CHARS:")
        print(response.text[:3000])
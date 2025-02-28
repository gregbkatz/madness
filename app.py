from flask import Flask, render_template, jsonify

app = Flask(__name__)

# NCAA Tournament team data for 2023
teams = {
    "west": [
        {"seed": 1, "name": "Kansas", "abbrev": "KU"},
        {"seed": 16, "name": "Howard", "abbrev": "HOW"},
        {"seed": 8, "name": "Arkansas", "abbrev": "ARK"},
        {"seed": 9, "name": "Illinois", "abbrev": "ILL"},
        {"seed": 5, "name": "Saint Mary's", "abbrev": "SMC"},
        {"seed": 12, "name": "VCU", "abbrev": "VCU"},
        {"seed": 4, "name": "UConn", "abbrev": "CONN"},
        {"seed": 13, "name": "Iona", "abbrev": "IONA"},
        {"seed": 6, "name": "TCU", "abbrev": "TCU"},
        {"seed": 11, "name": "Arizona St.", "abbrev": "ASU"},
        {"seed": 3, "name": "Gonzaga", "abbrev": "GON"},
        {"seed": 14, "name": "Gr. Canyon", "abbrev": "GCU"},
        {"seed": 7, "name": "Northwestern", "abbrev": "NW"},
        {"seed": 10, "name": "Boise State", "abbrev": "BSU"},
        {"seed": 2, "name": "UCLA", "abbrev": "UCLA"},
        {"seed": 15, "name": "UNC-Ash.", "abbrev": "UNCA"}
    ],
    "east": [
        {"seed": 1, "name": "Purdue", "abbrev": "PUR"},
        {"seed": 16, "name": "F. Dickinson", "abbrev": "FDU"},
        {"seed": 8, "name": "Memphis", "abbrev": "MEM"},
        {"seed": 9, "name": "Florida Atl.", "abbrev": "FAU"},
        {"seed": 5, "name": "Duke", "abbrev": "DUKE"},
        {"seed": 12, "name": "Oral Roberts", "abbrev": "ORU"},
        {"seed": 4, "name": "Tennessee", "abbrev": "TENN"},
        {"seed": 13, "name": "La.-Lafayette", "abbrev": "ULL"},
        {"seed": 6, "name": "Kentucky", "abbrev": "UK"},
        {"seed": 11, "name": "Providence", "abbrev": "PROV"},
        {"seed": 3, "name": "Kansas State", "abbrev": "KSU"},
        {"seed": 14, "name": "Montana St.", "abbrev": "MONT"},
        {"seed": 7, "name": "Michigan St.", "abbrev": "MSU"},
        {"seed": 10, "name": "USC", "abbrev": "USC"},
        {"seed": 2, "name": "Marquette", "abbrev": "MARQ"},
        {"seed": 15, "name": "Vermont", "abbrev": "UVM"}
    ],
    "south": [
        {"seed": 1, "name": "Alabama", "abbrev": "ALA"},
        {"seed": 16, "name": "TX A&M-CC", "abbrev": "TAMC"},
        {"seed": 8, "name": "Maryland", "abbrev": "MD"},
        {"seed": 9, "name": "W. Virginia", "abbrev": "WVU"},
        {"seed": 5, "name": "SDSU", "abbrev": "SDSU"},
        {"seed": 12, "name": "Charleston", "abbrev": "COFC"},
        {"seed": 4, "name": "Virginia", "abbrev": "UVA"},
        {"seed": 13, "name": "Furman", "abbrev": "FUR"},
        {"seed": 6, "name": "Creighton", "abbrev": "CREI"},
        {"seed": 11, "name": "NC State", "abbrev": "NCST"},
        {"seed": 3, "name": "Baylor", "abbrev": "BAY"},
        {"seed": 14, "name": "UCSB", "abbrev": "UCSB"},
        {"seed": 7, "name": "Missouri", "abbrev": "MIZ"},
        {"seed": 10, "name": "Utah State", "abbrev": "USU"},
        {"seed": 2, "name": "Arizona", "abbrev": "ARIZ"},
        {"seed": 15, "name": "Princeton", "abbrev": "PRIN"}
    ],
    "midwest": [
        {"seed": 1, "name": "Houston", "abbrev": "HOU"},
        {"seed": 16, "name": "N. Kentucky", "abbrev": "NKU"},
        {"seed": 8, "name": "Iowa", "abbrev": "IOWA"},
        {"seed": 9, "name": "Auburn", "abbrev": "AUB"},
        {"seed": 5, "name": "Miami", "abbrev": "MIA"},
        {"seed": 12, "name": "Drake", "abbrev": "DRKE"},
        {"seed": 4, "name": "Indiana", "abbrev": "IND"},
        {"seed": 13, "name": "Kent State", "abbrev": "KENT"},
        {"seed": 6, "name": "Iowa State", "abbrev": "ISU"},
        {"seed": 11, "name": "Pittsburgh", "abbrev": "PITT"},
        {"seed": 3, "name": "Xavier", "abbrev": "XAV"},
        {"seed": 14, "name": "Kenn. State", "abbrev": "KENN"},
        {"seed": 7, "name": "Texas A&M", "abbrev": "TAMU"},
        {"seed": 10, "name": "Penn State", "abbrev": "PSU"},
        {"seed": 2, "name": "Texas", "abbrev": "TEX"},
        {"seed": 15, "name": "Colgate", "abbrev": "COLG"}
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/teams')
def get_teams():
    return jsonify(teams)

if __name__ == '__main__':
    app.run(debug=True) 
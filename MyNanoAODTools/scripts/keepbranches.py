import json

# Define the branchsel content
branchsel_content = {
    "keep": [
        "run", 
        "event", 
        "luminosityBlock", 
        "Electron_pt", 
        "Electron_eta", 
        "Electron_phi", 
        "Electron_charge", 
        "Muon_pt", 
        "Muon_eta", 
        "Muon_phi", 
        "Muon_charge"
    ],
    "drop": [
        "*"
    ]
}

# Specify the file name
file_name = "branchsel.json"

# Write the JSON content to the file
with open(file_name, "w") as json_file:
    json.dump(branchsel_content, json_file, indent=4)

print(f"JSON data has been written to {file_name}")

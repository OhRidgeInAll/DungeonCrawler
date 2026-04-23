# firstProject
Learning Ursina Engine

# Running

## From the command line
First, install dependencies:
```shell
pip install -r requrirements.txt
```

Then execute the main file:
```shell
python main.py
```

## From a virtual environment (venv)

### First-time setup (run once)
Create the virtual environment:
```shell
python -m venv .venv
```

Install dependencies into it:
```shell
pip install -r requrirements.txt
```

### Each time you want to run the game
Activate the virtual environment:
```shell
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Run the game:
```shell
python main.py
```

When you're done, deactivate the virtual environment:
```shell
deactivate
```
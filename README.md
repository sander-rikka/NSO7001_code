# NSO7001_scripts
Collection of different scripts for "Remote Sensing of Earth Systems (NSO7001)" lecture at Taltech 

# Create virtual environment for course works
*Insert line by line*
```bash
python -m venv .venv
# UNIX source .venv/bin/activate   
# Windows venv\Scripts\activate     
python -m pip install --upgrade pip
pip install -r requirements.txt
```

# Working with git
### 1) Go to repo
cd NSO7001_code

### 2) See what they changed
git status

### 3) Save your HW1 work in a commit
git add HW1-atmosphere
git commit -m "My HW1 progress"

### 4) Get latest repo changes (new HW2 structure)
git pull --rebase origin main

That keeps your HW1 changes and updates HW2 from repo.

Optional safety backup before anything:

cp -R NSO7001_code NSO7001_code_backup
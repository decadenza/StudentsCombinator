import os
import sys
import logging
import time
import csv
import random
import math
import collections
from copy import deepcopy

# CONFIG
'''
You may need to change configuration accordingly.
'''
NUM_CHOICES_P = 3                         # Number of preferences for projects
NUM_CHOICES_W = 3                         # Number of preferences for work package
MAX_NUM_ITERATIONS = 10000                # Max iterations to find the best solution
# Cost parameters
# Cost is calculated as sum of 4 exponential terms
PENALTY_P = 3                           # Penalty assigned for lowering project (as exponent)
PENALTY_W = 3                           # Same for work-package (you can differenciate slightly from above)
PENALTY_CROSS = 9                       # Same correlating of both project and work-package
                                        # Increase if you have many students having lower choices
PENALTY_OVER = 12                       # Extra penalty for going over the last choice (as exponent)
                                        # Increase if you have unhappy students (none of their choices assigned)
                                        
# Others
CUR_PATH = os.path.dirname(os.path.realpath(__file__)) # Current path

if __name__ == "__main__":
    
    # Logging setup
    loggingTargets = logging.StreamHandler(sys.stdout), logging.FileHandler('log.txt', mode='w')
    logging.basicConfig(format='%(message)s', level=logging.INFO, handlers=loggingTargets)
    
    logging.info('StudentCombinator (c) 2019-2020 by Pasquale Lafiosca\n')
    
    if not os.path.isfile(os.path.join(CUR_PATH,'Preferences.csv')):
        logging.error('File "Preferences.csv" not found.')
        exit()

    if not os.path.isfile(os.path.join(CUR_PATH,'Slots.csv')):
        logging.error('File "Slots.csv" not found.')
        exit()
    
    
    # Read projects and work packages
    with open(os.path.join(CUR_PATH,'Slots.csv'), 'r', newline='', encoding='utf8', errors='ignore') as slot:
        sReader = csv.reader(slot, delimiter=';', quotechar='"')
        listW = next(sReader)[1:]   # List of Work Packages
        listP = []                  # List of Projects
        slot = []                   # Available slots
        for row in sReader:
            listP.append(row[0])
            slot.append( list(map(int,row[1:]) ))
    
    with open( os.path.join(CUR_PATH,'Preferences.csv'), 'r', newline='', encoding='utf8', errors='ignore') as pref:
        pReader = csv.reader(pref, delimiter=';', quotechar='"')
        prefHeader = next(pReader)[0:3] # Skip header and save data if for later
        prefData = []
        pref = []
        for row in pReader:
            prefData.append(row[0:3])
            pref.append(row[3:])   # Rows are student, cols are choices
    
    totP = len(listP)
    totW = len(listW)
    totSlot = sum([e for row in slot for e in row])
    totStudent = len(pref)
    
    logging.info(f"# of students: {totStudent}")
    logging.info(f"# of projects: {totP}")
    logging.info(f"# of project choices: {NUM_CHOICES_P}")
    logging.info(f"# of work-packages: {totW}")
    logging.info(f"# of work-packages choices: {NUM_CHOICES_W}")
    logging.info("Processing...")
    
    if totSlot != totStudent:
        logging.error(f"ERROR: The number of students is {totStudent}, while the available slots are {totSlot}. Please correct the values.")
        exit()
    
    studentIndex = list(range(totStudent))
    
    # Get the preferences by index. Rows are choices, cols are students.
    prefP = [ [ totP for _ in range(totStudent) ] for _ in range(NUM_CHOICES_P) ]  # Initialised with NO CHOICE = totP
    prefW = [ [ totW for _ in range(totStudent) ] for _ in range(NUM_CHOICES_W) ]  # Initialised with NO CHOICE = totW
    
    for i, row in enumerate(pref):
        for j,col in enumerate( row[:NUM_CHOICES_P] ):
            try:
                prefP[j][i] = listP.index(pref[i][j])
            except ValueError:
                logging.warning("WARNING: \"{}\" at row {} is not in Projects list. No priority given.".format(pref[i][j], i+2))
                prefP[j][i] = None # Empty or Invalid choice given
        for j,col in enumerate( row[NUM_CHOICES_P:NUM_CHOICES_P+NUM_CHOICES_W] ):
            try:
                prefW[j][i] = listW.index(pref[i][j+NUM_CHOICES_P])
            except ValueError:
                logging.warning("WARNING: \"{}\" at row {} is not in Work Packages list. No priority given.".format(pref[i][j+NUM_CHOICES_P], i+2))
                prefW[j][i] = None # Empty or Invalid choice given
    
    # Get all available slots per project
    availableP = [sum(row) for row in slot]             # Ordered list of slots numbers for projects
    
    
    ####################END#OF#PRE#PROCESSING##############################################################################
    
    # Initialization
    cost = float('inf')
    
    bestAssignedP = None
    bestAssignedW = None
    bestAssignedChoiceP = None
    bestAssignedChoiceW = None
    
    for counter in range(MAX_NUM_ITERATIONS):    
        
        random.shuffle(studentIndex) # Random initialisation of student order!
        
        assignedP = [ None ] * totStudent
        assignedW = [ None ] * totStudent
        assignedChoiceP = [ None ] * totStudent
        assignedChoiceW = [ None ] * totStudent
        remainingP = availableP.copy()
        remainingW = deepcopy(slot)
        
        # Temporary assignments P
        for i in studentIndex:
            if assignedP[i] is None:
                for choice in range(NUM_CHOICES_P):
                    if prefP[choice][i] is not None and remainingP[prefP[choice][i]]>0:
                        assignedP[i] = prefP[choice][i]
                        assignedChoiceP[i] = choice
                        remainingP[prefP[choice][i]]-=1
                        break
            
        # Fill empty P
        for p,r in enumerate(remainingP):
            for _ in range(r):
                try:
                    i = assignedP.index(None)
                except ValueError:
                    logging.error("ERROR: Number of remaining students does not match remaining projects.")
                    exit()
                else:
                    assignedP[i] = p
                    # Look if there are empty/invalid preferences, else consider as random choice.
                    assignedChoiceP[i] = next( (c for c in range(NUM_CHOICES_P) if prefP[c][i]==None), NUM_CHOICES_P) 
            
        
        # REVERSE THE LIST! If you had a bad project, you get a better work package
        studentIndex.reverse()
        
        # Temporary assignments WP
        for i in studentIndex:
            if assignedW[i]==None:
                for choice in range(NUM_CHOICES_W):
                    if prefW[choice][i] is not None and remainingW[assignedP[i]][prefW[choice][i]]>0:
                        assignedW[i] = prefW[choice][i]
                        assignedChoiceW[i] = choice
                        remainingW[assignedP[i]][prefW[choice][i]]-=1
                        break
        
        
        
        # Fill empty WP
        for p in range(totP):
            for w in range(totW):
                for _ in range(remainingW[p][w]):
                    i = next( (x for x in studentIndex if assignedW[x]==None and assignedP[x]==p) , None )
                    if i is None:
                        logging.error("ERROR: Number of remaining students does not match remaining work-packages.")
                        exit()
                    else:
                        assignedW[i] = w
                        assignedChoiceW[i] = next( (c for c in range(NUM_CHOICES_W) if prefW[c][i]==None), NUM_CHOICES_W) # Look if there are empty preferences, else assign after last choice.
                        #assignedChoiceW[i] = NUM_CHOICES_W
        
        
        
        #################################
        ### OPTIMIZATION REPLACEMENTS ###
        #################################
        
        while(True):
            doneReplacements = False
            replacements = []
            exclusions = set()
            
            # Swap PROJECT
            for i in [x for x in studentIndex if assignedChoiceP[x]==NUM_CHOICES_P]: # Students that got the lowest choice (higher value)
                for b in range(NUM_CHOICES_P): # In order, first choice is preferable
                    if prefP[b][i]==None:      # If any choice is empty, you can proceed (it means "whatever")
                        continue
                    
                    try: # Find a compatible exchange: a different student with assigned project compatible with i's choices WITHIN THE SAME WP (not already to be exchanged with someone else)
                        r = next( (s,lowerChoice,) for lowerChoice in range(NUM_CHOICES_P) for s in studentIndex if s!=i and s not in exclusions and assignedP[s]==prefP[b][i] and assignedW[s]==assignedW[i] and ( prefP[lowerChoice][s] == assignedP[i] or prefP[lowerChoice][s]==None ) ) 
                    except StopIteration:
                        continue
                    else:
                        replacements.append((i,r[0],b,r[1],))
                        exclusions.add(r[0])
                    break # IMPORTANT TO BREAK HERE
            
            if replacements:
                doneReplacements=True 
                # Do replacements
                for i, j, iNewChoice, jNewChoice in replacements:
                    tempP = assignedP[i]
                    assignedP[i] = assignedP[j]         # Assign a better project
                    assignedChoiceP[i] = iNewChoice     # And its choice number
                    assignedP[j] = tempP             # Decrease the preference of the other r student
                    assignedChoiceP[j] = jNewChoice  # And his choice
                    
            # Swap WORK PACKAGE 
            replacements = []
            exclusions = set()
            for i in [x for x in studentIndex if assignedChoiceW[x] == NUM_CHOICES_W]: # Students that get last choice
                for b in range(NUM_CHOICES_W): # Better choices
                    if prefW[b][i]==None:
                        continue
                    try: # Find first compatible replacement WITHIN SAME PROJECT
                        r = next( (s,lowerChoice,) for lowerChoice in range(NUM_CHOICES_W) for s in studentIndex if s!=i and s not in exclusions and assignedW[s]==prefW[b][i] and assignedP[i]==assignedP[s] and ( prefW[lowerChoice][s] == assignedW[i] or prefW[lowerChoice][s]==None ) ) 
                    except StopIteration:
                        continue
                    else:
                        replacements.append((i,r[0],b,r[1],))
                        exclusions.add(r[0])
                    break # IMPORTANT TO BREAK HERE
            
            
            if replacements:
                doneReplacements=True
                # Do replacements
                for i, j, iNewChoice, jNewChoice in replacements:
                    tempW = assignedW[i]
                    assignedW[i] = assignedW[j]         # Assign a better project
                    assignedChoiceW[i] = iNewChoice     # And its choice number
                    assignedW[j] = tempW             # Decrease the preference of the other r student
                    assignedChoiceW[j] = jNewChoice  # And his choice
            
            

            # If not replacements where done in both P and W
            if not doneReplacements:
                break # Exit from optimisation loop
        
        # CALCULATE COST
        newCost = sum((math.pow(x,PENALTY_P) for x in assignedChoiceP)) + sum((math.pow(x,PENALTY_W) for x in assignedChoiceW))
        newCost += sum((math.pow(x+y,PENALTY_CROSS) for x in assignedChoiceP for y in assignedChoiceW))
        newCost += sum( (math.pow(assignedChoiceP[i]+assignedChoiceW[i],PENALTY_OVER) for i in range(totStudent) if assignedChoiceP[i]==NUM_CHOICES_P or assignedChoiceW[i]==NUM_CHOICES_W) )
        
        #newCost = sum((math.pow(PENALTY_P,x) for x in assignedChoiceP)) + sum((math.pow(PENALTY_W,y) for y in assignedChoiceW))
        #newCost += sum((math.pow(PENALTY_CROSS,x+y) for x in assignedChoiceP for y in assignedChoiceW))
        
        if newCost < cost:
            logging.info(f"Cost lowered to {newCost} at iteration {counter+1}")
            cost = newCost
            bestAssignedP = assignedP.copy()
            bestAssignedW = assignedW.copy()
            bestAssignedChoiceP = assignedChoiceP.copy()
            bestAssignedChoiceW = assignedChoiceW.copy()
       
        
# Reassign string values to project and work-package
assignedTextP = [None] * totStudent
assignedTextW = [None] * totStudent
for i in range(totStudent):
    assignedTextP[i] = listP[bestAssignedP[i]]
    assignedTextW[i] = listW[bestAssignedW[i]]
    
        
# Print to file
with open(os.path.join(CUR_PATH,'ASSIGNMENTS.csv'), 'w', newline='', encoding='utf8', errors='ignore') as output:
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
    
    writer.writerow(prefHeader + ['Assigned Project', 'Assigned Work Package','Assigned Project Choice #', 'Assigned Work Package Choice #'] + ["Original Project Choice #{}".format(i+1) for i in range(NUM_CHOICES_P)] + ["Original Work Package Choice #{}".format(i+1) for i in range(NUM_CHOICES_W)]) 
    
    for i in range(totStudent):
        writer.writerow( prefData[i] + [ assignedTextP[i], assignedTextW[i], bestAssignedChoiceP[i]+1, bestAssignedChoiceW[i]+1 ] + pref[i] )




# Stats printing
statsP = {x:bestAssignedChoiceP.count(x) for x in range(NUM_CHOICES_P+1)}
statsW = {x:bestAssignedChoiceW.count(x) for x in range(NUM_CHOICES_W+1)}
logging.info("\n\n----------FINAL STATS----------")
logging.info("Projects:")
for n in range(NUM_CHOICES_P+1):
    logging.info("\t{} ({:.2f}%)\tstudents got his #{} choice of project.".format(statsP[n], (100*statsP[n])/totStudent, n+1))
logging.info("Work Packages:")
for n in range(NUM_CHOICES_W+1):
    logging.info("\t{} ({:.2f}%)\tstudents got his #{} choice of work-package.".format(statsW[n], (100*statsW[n])/totStudent, n+1))
# Specific stats
logging.info("Combined choices:")
for p in range(NUM_CHOICES_P+1):
    for w in range(NUM_CHOICES_W+1):
        c = len([i for i in range(totStudent) if bestAssignedChoiceP[i]==p and bestAssignedChoiceW[i]==w])
        logging.info(f"\t{c}\tstudents got #{p+1} project and #{w+1} work-package.")

input("\nDONE!\nPress a key to exit...")





# pyomo solve --solver=glpk --summary Scheduling.py scheduling.dat

from pyomo.environ import *

model = AbstractModel() #abstract model means the data is in a different place.

# param n; #jobs 
model.NumJobs = Param(within = PositiveReals)

# param m; #machines
model.NumMachines = Param(within = PositiveReals)

#Python will not let you index a paramater with a paramater.  Has to be a set.
#this creates the set of jobs from 1 to NumJobs

model.Jobs = RangeSet(1,model.NumJobs) 

model.Machines = RangeSet(1,model.NumMachines)

# param a {1..m, 1..n}; order of machines  a(1,2) = 3  would be the 1st machine to work on job 2 is machine 3
model.a = Param(model.Machines, model.Jobs)

# Param P  processing time    P(1,2) = 3 would mean processing time for job 1 on machine 2 is 3 
model.p = Param (model.Machines, model.Jobs)

# Big M
model.BigM = Param()

#var t{1..m, 1..n} >= 0; Completion Time of Machine m working on job n
model.t = Var (model.Machines, model.Jobs, within=NonNegativeReals)

#var s{1..m, 1..n} >= 0; Start time for machine m on job n
model.s = Var (model.Machines, model.Jobs, within=NonNegativeReals)

#var y{1..m, 1..n, 1..n}, binary; 1 if machine m works on job n before job n+1.  
model.y = Var (model.Machines, model.Jobs, model.Jobs, within=Binary)

#minimize Sum: sum {j in 1..n} t[a[m, j], j];  
#sum of completion time t of the a'th machine to work on each job j for all jobs j
#creates the objective functioin

def BuildObjective(model):
  obj = 0.0  
  for j in model.Jobs:
      obj += model.t[model.a[model.NumMachines,j],j]  #"obj +=" means summerize over 
  return obj

#tells pyomo that the objective is defined by the rule "def BuildObjective"
model.obj = Objective(rule=BuildObjective)


#creates the constraints StartAfterFinish {j in 1..n, k in 2..m}: s[a[k, j], j] >= t[a[k - 1, j], j]
def StartAfterFinish(model, j, k):
    if k >= 2:
        return model.s[model.a[k,j],j] >= model.t[model.a[k-1,j],j]
    else:
        return Constraint.Skip
        
model.StartAfterFinish = Constraint(model.Jobs, model.Machines, rule=StartAfterFinish)

#subject to StartFinish {i in 1..m, j in 1..n}: s[i, j] = t[i, j] - p[i, j];
def StartFinish(model, machineM, jobJ):
    return model.s[machineM, jobJ] == model.t[machineM, jobJ] - model.p[machineM, jobJ]
model.StartFinish = Constraint(model.Machines, model.Jobs, rule=StartFinish)

#subject to BigM1 {i in 1..m, j in 1..n, k in 1..n}: 
#						s[i, k] >= t[i, j] - y[i, j, k] * M;
def BigM1(model, machineM, jobJ, jobK):
    return model.s[machineM, jobK] >= model.t[machineM, jobJ] - model.y[machineM, jobJ, jobK]*model.BigM
model.BigM1 = Constraint(model.Machines, model.Jobs, model.Jobs, rule=BigM1)


#subject to BigM2 {i in 1..m, j in 1..n, k in j+1..n}: 
#						s[i, j] >= t[i, k] - (1 - y[i, j, k]) * M;

def BigM2(model, machineM, jobJ, jobK):
    if jobK >= jobJ+1:
        return model.s[machineM, jobJ] >= model.t[machineM, jobK] - (1 - model.y[machineM, jobJ, jobK])*model.BigM
    else:
        return Constraint.Skip
model.BigM2 = Constraint(model.Machines, model.Jobs, model.Jobs, rule=BigM2)

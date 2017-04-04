import sys
import os
import collections
import random
dfile=sys.argv[1]
path='/'.join(dfile.split('/')[:-1])
data=[]#collections.defaultdict(dict)
nins=0
userdict={}
itemdict={}
with open(dfile, 'r') as f:
    for line in f:
        tks=line.split('::')
        user,item, rate=tks[0], tks[1], tks[2]
        if user not in userdict:
            userdict[user]=len(userdict)
        user=str(userdict[user])

        if item not in itemdict:
            itemdict[item]=len(itemdict)
        item=str(itemdict[item])
        data.append([user, item, rate]) 
        nins+=1
print nins
tr_ins=random.sample(range(nins), int(0.9*nins))
te_ins=list(set(range(nins))-set(tr_ins))
print len(tr_ins)
print len(te_ins)
dftr=path+'/'+dfile.split('/')[-1]+'.random.tr'
dfte=path+'/'+dfile.split('/')[-1]+'.random.te'
wtr=0
wte=0
with open(dftr, 'w') as tfw:
    for i in tr_ins:        
        u,i,r=data[i]
        tfw.write('%s\t%s\t%s\n' %(u, i, r))
        wtr+=1
tfw.close()
with open(dfte, 'w') as tfw:
    for i in te_ins:        
        u,i,r=data[i]
        tfw.write('%s\t%s\t%s\n' %(u, i, r))
        wtr+=1

tfw.close()

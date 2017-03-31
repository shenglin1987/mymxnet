import os

if __name__=='__main__':
    eta=[0.001, 0.01]
    upass=[2,5,10]
    ipass=[2,5,10]
    num_embed=[10,30,50,100]
    num_hidden=[10,30,50,100]
    for e in eta:
        for u in upass:
            for i in ipass:
                for embed in num_embed:
                    for hidden in num_hidden:
                        os.system('python cdmemnn.py -train ~/Data/ml-1m/ratings.dat.tr -val ~/Data/ml-1m/ratings.dat.te -eta %f -upass %d -ipass %d -nembed %d -nhidden %d &' %(e,u,i,embed,hidden))

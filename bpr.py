import mxnet as mx
import numpy as np
import random
import sys,logging
import collections
class Batch:
    def __init__(self, data_names, data, label_names, label):
        self.data_names=data_names
        self.label_names=label_names
        self.data=data
        self.label=label

    def provide_data(self):
        return [(n,x.shape) for n,x in zip(self.data_names,self.data)]

    def provide_label(self):
        return [(n,x.shape) for n,x in zip(self.label_names,self.data)]

class DataIter(mx.io.DataIter):
    def __init__(self, data, batch_size):
        super(DataIter, self).__init__()
        self.batch_size=batch_size

        self.data=data

        self.provide_data=[('user',(self.batch_size,)),('pos_item', (self.batch_size,)), ('neg_item', (self.batch_size,))]

        self.provide_label=[('score',(self.batch_size,))]

    def __iter__(self):
        for k in xrange(len(self.data)/self.batch_size):
            users=[]
            pos_items=[]
            neg_items=[]
            scores=[]
            for i in xrange(self.batch_size):
                j=self.batch_size*k+i
                user, pos_item, neg_item=self.data[j]
                users.append(user)
                pos_items.append(pos_item)
                neg_items.append(neg_item)
                scores.append(1)
            data_all=[mx.nd.array(users),mx.nd.array(pos_items), mx.nd.array(neg_items)]
            data_names=['user','pos_item', 'neg_item'] 
            label_all=[mx.nd.array(scores)]
            label_names=['score']
            data_batch=Batch(data_names, data_all, label_names, label_all)
            yield data_batch

    def reset(self):
        random.shuffle(self.data)

def get_network(num_hidden, max_user, max_item):
    user=mx.sym.Variable('user')
    pos_item=mx.sym.Variable('pos_item')
    neg_item=mx.sym.Variable('neg_item')

    user_weight=mx.sym.Variable('user_weight')
    item_weight=mx.sym.Variable('item_weight')
    user=mx.sym.Embedding(data=user, input_dim=max_user, weight=user_weight, output_dim=num_hidden)

    pos_item=mx.sym.Embedding(data=pos_item, input_dim=max_item, weight=item_weight, output_dim=num_hidden)
    neg_item=mx.sym.Embedding(data=neg_item, input_dim=max_item, weight=item_weight, output_dim=num_hidden)

    item_diff=neg_item-pos_item
    res=user*item_diff
    res=mx.sym.sum_axis(data=res, axis=1)
    res=mx.sym.Flatten(data=res)
    res=mx.sym.MakeLoss(res)
    return res

def convert_data(user, item, user_dict, item_dict):
    if user not in user_dict:
        user_dict[user]=len(user_dict)
    user=user_dict[user]
    if item not in item_dict:
        item_dict[item]=len(item_dict)
    item=item_dict[item]
    return (user, item)

def cal_AUC(user, scores, pos_items, max_item, ignore=None):
    scores=mx.nd.array(scores).reshape((1,max_item))
    #print scores.shape
    candidates=mx.nd.argsort(scores, is_ascend=False).asnumpy()[0]
    #print candidates
    #print candidates.shape
    res=0.0
    if ignore:
        max_item-=len(ignore)
    total=len(pos_items)*(max_item-len(pos_items))
    hit=0.0
    num_correct_pairs=0.0
    for i in xrange(max_item):
        if ignore and candidates in ignore:
            continue
        if candidates[i] in pos_items:
            hit+=1
        else:
            num_correct_pairs+=hit
    res=num_correct_pairs/total
    return res
    



def train(data, user_pos,max_user,max_item, network, batch_size, num_epoch, learning_rate):
    network=mx.mod.Module(network, data_names=('user','pos_item', 'neg_item'),context=mx.gpu())
    network.bind(data_shapes=[('user',(batch_size,)),('pos_item', (batch_size,)), ('neg_item', (batch_size,))])
    init=mx.init.Xavier(factor_type='in', magnitude=1)
    network.init_params(initializer=init)
    network.init_optimizer(optimizer='adam', kvstore=None, optimizer_params={'learning_rate':1E-3, 'wd':1E-4})
    for i in xrange(num_epoch):
        batch_data=random.sample(data, batch_size)
        u=mx.nd.array([x[0] for x in batch_data])		
        p=mx.nd.array([x[1] for x in batch_data])		
        n=mx.nd.array([x[2] for x in batch_data])		
        network.forward(data_batch=mx.io.DataBatch(data=[u,p,n],label=['user','pos_item','neg_item']), is_train=True)
        outputs=network.get_outputs()
        network.backward()
        logging.info("Iter:%d, Error:%f" %(i,outputs[0].asnumpy().sum()/(batch_size+0.0)))	
        if i%50==0:
            params=network.get_params()[0]
            for x in params:
                if x=='user_weight':
                    user_params=params[x]
                if x=='item_weight':
                    item_params=params[x]
            res=mx.nd.dot(user_params, item_params.T).asnumpy()
        #    print res.shape
            auc=0.0
            for u in xrange(max_user):
         #       print u
                auc_u=cal_AUC(u,res[u,:],user_pos[u], max_item)
                auc+=auc_u
            print 'Iterations %d, AUC on training %f' %(i, auc/res.shape[0])
        network.update()





user_pos_item=collections.defaultdict(set)
data_file=sys.argv[1]
user_dict={}
item_dict={}
data=[]
with open(data_file, 'r') as f:
    for line in f:
        tks=line.strip().split('\t')
        user, pos_item=convert_data(tks[0],tks[1],user_dict, item_dict)
        data.append([user, pos_item])
        user_pos_item[user].add(pos_item)
max_user=len(user_dict)
max_item=len(item_dict)
print '#User ', max_user
print '#Item ', max_item
for i in xrange(len(data)):
    u,p=data[i]
    n=random.choice(range(max_item))
    while n in user_pos_item[u]:
        n=random.choice(range(max_item))
    data[i]=(u,p,n)

num_hidden=64
num_epoch=2000
batch_size=100
learning_rate=0.01
net=get_network(num_hidden, max_user, max_item)
train(data,user_pos_item, max_user, max_item, net, batch_size, num_epoch, learning_rate)







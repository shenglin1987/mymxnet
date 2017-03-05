import logging
import random
import numpy as np
import mxnet as mx
from datautils import Seq2SeqIter, default_build_vocab
from seq2seq import Seq2Seq


CTX = mx.cpu()

def main(**args):
    vocab, vocab_rsd = default_build_vocab('./data/vocab.txt')
    vocab_size = len(vocab)
    print 'vocabulary size is %d' % vocab_size
    data = Seq2SeqIter(data_path='./data/data.pickle', source_path='./data/a.txt',
                       target_path='./data/b.txt', vocab=vocab,
                       vocab_rsd=vocab_rsd, batch_size=10, max_len=25,
                       data_name='data', label_name='label', split_char='\n',
                       text2id=None, read_content=None, model_parallel=False)
    print 'training data size is %d' % data.size
    model = Seq2Seq(seq_len=25, batch_size=10, num_layers=1,
                    input_size=vocab_size, embed_size=150, hidden_size=150,
                    output_size=vocab_size, dropout=0.0, mx_ctx=CTX)
    model.train(dataset=data, epoch=5)


if __name__ == "__main__":
    main()

import os,getopt
import sys
sys.path.insert(0, "../")
import numpy as np
import logging
logging.basicConfig(level=logging.ERROR,format='%(asctime)s %(name)s  %(levelname)s %(message)s')

if __name__ == '__main__':
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "g:b:d:m:u:", ["gpu=","batch_size=","data=","mode=","univar="])
    except:
        print(u'input error!')
        sys.exit(2)
    
    gpu = None
    batch_size = None
    data = None
    mode = None
    univar = False
    
    for opt, arg in opts:
        if opt in ['-g','--gpu']:
            gpu = arg
        elif opt in ['-b','--batch_size']:
            batch_size = int(arg)
        elif opt in ['-d','--data']:
            data = arg
        elif opt in ['-m','--mode']:
            mode = arg
        elif opt in ['-u','--univar']:
            univar = bool(int(arg))
        else:
            print(u'input error!')
            sys.exit(2)
    
    if gpu is None or batch_size is None or data is None or mode is None:
        print(u'input error!')
        sys.exit(2)
    
    os.environ["CUDA_VISIBLE_DEVICES"]=gpu
    from src.utils import dataset_loader
    from src.core.model import GTT
    import tensorflow as tf
    
    input_len = 720
    pred_len = 720
    if data == 'h1':
        _,_,test_df,signals = dataset_loader.load_ett_data(name='ETTh1.csv',uni=univar)
    elif data == 'h2':
        _,_,test_df,signals = dataset_loader.load_ett_data(name='ETTh2.csv',uni=univar)
    elif data == 'm1':
        _,_,test_df,signals = dataset_loader.load_ett_data(name='ETTm1.csv',uni=univar)
    elif data == 'm2':
        _,_,test_df,signals = dataset_loader.load_ett_data(name='ETTm2.csv',uni=univar)
    elif data == 'electricity':
        _,_,test_df,signals = dataset_loader.load_electricity_data(uni=univar)
    elif data == 'traffic':
        _,_,test_df,signals = dataset_loader.load_traffic_data(uni=univar)
    elif data == 'weather':
        _,_,test_df,signals = dataset_loader.load_weather_data(uni=univar)
    elif data == 'exchange_rate': # добавил exchange_rate
        _,_,test_df,signals = dataset_loader.load_exchange_rate_data(uni=univar) # добавил exchange_rate
        #---------------------------------------------------------------добавил de_big-------------------------------------
    if data == 'de_big': 
        _,_,test_df,signals = dataset_loader.load_de_big_data(uni=univar)
    elif data == 'ill':
        _,_,test_df,signals = dataset_loader.load_illness_data(uni=univar)
        input_len = 60
        pred_len = 60
         #---------------------------------------------------------------добавил de_small-------------------------------------
    elif data == 'de_small':
        _,_,test_df,signals = dataset_loader.load_de_small_data(uni=univar)
        input_len = 60
        pred_len = 60
    
    foundation_path= f'../checkpoints/GTT-{mode}'
    strategy = tf.distribute.MirroredStrategy()
    with strategy.scope():
        model = GTT.from_tsfoundation(signals, foundation_path)
        y_pred,y_true = model.predict(test_df,input_len,pred_len,batch_size=batch_size)
    
    if pred_len == 720:
        pred_lens = [24,96,192,336,720] # добавил новый шаг предсказания
    else:
        pred_lens = [24,36,48,60]
    
    maes = []
    mses = []
    for pred_len in pred_lens:
        mae = np.mean(np.abs(y_pred[:,:pred_len,:]-y_true[:,:pred_len,:]))
        mse = np.mean(np.square(y_pred[:,:pred_len,:]-y_true[:,:pred_len,:]))
        print(pred_len) # добавил вывод о дальности прогноза
        print('mae', mae, 'mse', mse) # свёл в одну строку
        print('-'*20) #добавил разделитель для лучшей читаемости 
        maes.append(mae)
        mses.append(mse)
    print('mae mean',np.mean(maes))
    print('mse mean',np.mean(mses))
    print()


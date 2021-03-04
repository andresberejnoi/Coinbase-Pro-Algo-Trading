import pandas as pd
import cbpro

import streamz
#from streamz import Stream
import streamz.dataframe

from holoviews.streams import Pipe, Buffer

class GraphicWebsocketClient(cbpro.WebsocketClient):
    CBPRO_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'   #this parses the string date returned by Coinbase Pro into a pandas datetime object
    def __init__(self,datastream=None,sandbox_mode=True,**kwargs):
        super().__init__(**kwargs)
        self.datastream = datastream
        self.sandbox_mode = sandbox_mode
        self._set_update_function()
    
    @property 
    def _datastream_type(self):
        return type(self.datastream)

    def on_open(self):
        if self.sandbox_mode:
            self.url = 'wss://ws-feed-public.sandbox.pro.coinbase.com'
        else:
            self.url = 'wss://ws-feed.pro.coinbase.com'
        self.message_count = 0
    
    def _set_update_function(self):
        #print(type(self.datastream))
        if isinstance(self.datastream,Buffer):
            #print("Datastream of type: Buffer")
            self._updater_func = self._update_buffer
        
        elif isinstance(self.datastream,streamz.dataframe.DataFrame):
            #print("Datastream of type: Streaming DataFrame")
            self._updater_func = self._update_stream_df
        
        elif isinstance(self.datastream,streamz.core.Stream):
            #print("Datastream of type: Stream")
            self._updater_func = self._update_core_stream
        
        elif isinstance(self.datastream, dict):
            self._updater_func = self._update_dict
        
        else:
            print(f"Unsupported Datastream of type: {self._datastream_type}")
            self._updater_func = self._update_print
            return

        print(f"Datastream of type: {self._datastream_type}")

    def _update_print(self,**kwargs):
        price_val = kwargs.get('price',None)
        time_val  = kwargs.get('time',None)
        print(f"DUDE {time_val} {price_val}")

    def _update_buffer(self, **kwargs):
        price_val = kwargs.get('price',None)
        time_val  = kwargs.get('time',None)
        
        self.datastream.send(pd.DataFrame({       # .send() works for Buffer objects
                'timestamp':[time_val],
                'price'    :[price_val],
            }).set_index('timestamp'))

    def _update_stream_df(self, **kwargs):
        price_val = kwargs.get('price',None)
        time_val  = kwargs.get('time',None)
        
        self.datastream.emit(pd.DataFrame({       # .emit() is for Stream objects
                'timestamp':[time_val],
                'price'    :[price_val]
            }).set_index('timestamp'))
        
    
    def _update_core_stream(self,**kwargs):
        price_val = kwargs.get('price',None)
        time_val  = kwargs.get('time',None)

        self.datastream.emit([time_val,price_val])

    def _update_dict(self,**kwargs):
        self.datastream.update(kwargs)

    def on_message(self,msg):
        self.message_count += 1
        msg_type = msg.get('type',None)
        if msg_type == 'ticker':
            time_val   = msg.get('time',None)
            time_val   = pd.Timestamp(time_val)#,format=self.CBPRO_DATE_FORMAT)
            
            price_val  = msg.get('price',None)
            price_val  = float(price_val)
            #print(time_val,price_val)
            
            self._updater_func(price=price_val,time=time_val)
 
    def on_close(self):
        print(f"<---Websocket connection closed--->\n\tTotal messages: {self.message_count}")

if __name__ == '__main__':
    print('Nothing to execute')
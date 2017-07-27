import paho.mqtt.client as mqtt
import serial
import  time

class buf_class():
    def __init__(self):
        self.buf_size = 1024*10
        self.buf = [0 for x in range(self.buf_size)]
        self.write_point = 0
        self.read_point = 0
        self.ov_flag=False
        self.buf_lock=False

    def write_buf(self,string):
        #print self.write_point ,self.read_point
        i=0
        j=0
        while self.buf_lock:
            pass
        self.buf_lock=True
        cnt = len(string)
        if(cnt>self.buf_size):
            #print 'cnt>self.buf_size'
            string=string[cnt-self.buf_size:cnt]
            cnt=self.buf_size

        # ov
        if(self.write_point<self.read_point):
            if(self.write_point+cnt>self.read_point):
                self.ov_flag=True
        elif(self.write_point>self.read_point):
            if(self.write_point+cnt>self.buf_size+self.read_point):
                self.ov_flag=True

        # write buf
        if (self.write_point + cnt >= self.buf_size):
            cnt = self.write_point + cnt - self.buf_size
            rest_cnt = self.buf_size - self.write_point
            for i in range(rest_cnt):
                self.buf[self.write_point] = string[i]
                self.write_point += 1
            if rest_cnt>0:
                i+=1

            if cnt > 0:
                self.write_point = 0

        for j in range(cnt):
            self.buf[self.write_point] = string[i+j]
            self.write_point += 1
        if cnt>0:
            j+=1
        self.buf_lock = False
        return i+j

    def read_buf(self,cnt):
        #print self.read_point,self.write_point
        while self.buf_lock:
            pass
        self.buf_lock=True
        result = ''
        if self.ov_flag:
            self.read_point=self.write_point
            self.ov_flag=False
        else:
            if(self.read_point==self.write_point):
                self.buf_lock=False
                return ''
        if(self.read_point>=self.write_point):
            if(self.read_point+cnt<self.buf_size):
                result+=''.join(self.buf[self.read_point:self.read_point+cnt])
                self.read_point+=cnt
            else:
                cnt=self.read_point+cnt-self.buf_size
                rest_cnt=self.buf_size-self.read_point
                result += ''.join(self.buf[self.read_point:self.read_point + rest_cnt])
                self.read_point +=rest_cnt
                #print cnt
                #if(cnt>0):
                self.read_point=0

        if(self.read_point<self.write_point):
            if(self.read_point+cnt<self.write_point):
                real_cnt=cnt
            else:
                real_cnt=self.write_point-self.read_point
            result += ''.join(self.buf[self.read_point:self.read_point + real_cnt])
            self.read_point += real_cnt

        self.buf_lock=False
        return result
    def read_ex_un(self,ex='',un='',delay_time=1):
        result=''
        match_cnt=0
        if ex!='':
            start_time=time.time()
            while 1:
                if time.time()-start_time>=delay_time:
                    raise Exception("time out")
                temp=self.read_buf(1)
                if temp!=None:
                    if temp==ex[match_cnt]:
                        match_cnt+=1
                else:
                    match_cnt=0

                if(match_cnt==len(ex)):
                    match_cnt = 0
                    break
        start_time = time.time()
        while 1:
            if time.time() - start_time >= delay_time:
                raise Exception("time out")
            temp = self.read_buf(1)
            if temp != '':
                result+=temp
                if temp == un[match_cnt]:
                    match_cnt += 1
            else:
                match_cnt = 0

            if (match_cnt == len(un)):
                break
        return result



class mqtt_class():
    def __init__(self):
        #print 'mqtt init'
        self.log_name =''
        self.topic_pub=''
        self.topic_sub=''
        #self.buf = buf_class()
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    def log_conf(self,log_name):
        self.log_name=log_name

    def connect(self,ip='',port=1883,topic_sub='',topic_pub=''):
        self.ser = serial.Serial('COM25', 115200, timeout=0.1)
        self.topic_sub=topic_sub
        self.topic_pub=topic_pub
        self.client.connect(ip, port, 60)
        self.client.loop_start()
        time.sleep(0.1)
    def close(self):
        self.client.disconnect()
        self.client.loop_stop()


    def on_connect(self,client, userdata, flags, rc):
        #print("Connected with result code "+str(rc))
        if rc==0:
            #print 'connected'
            client.subscribe(self.topic_sub)

    def on_message(self,client, userdata, msg):
        #self.buf.write_buf(str(msg.payload))
        self.ser.write(str(msg.payload))
        #self.log_mqtt(str(msg.payload))

    def send(self,payload=''):
        self.client.publish(self.topic_pub,payload)
    def read_ex_un(self,ex='', un='', delay_time=1):
        return  self.buf.read_ex_un( ex, un, delay_time)
    def log_mqtt(self,string):
        if len(string) > 0:
            fd = open(self.log_name, 'ab+')
            fd.write(string)
            fd.close()
if __name__ == "__main__":
    try:
        C = mqtt_class()
        C.connect('10.220.52.33', 1883, 'serial/output01', 'serial/input01')

    except:
        print "connect fail"
    else:
        print "connect success"
        while 1:
            res = C.ser.read(1)
            if res != '':
                C.send(res )
    C.ser.close()
    C.close()
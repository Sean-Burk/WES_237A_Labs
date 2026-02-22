import multiprocessing as mp
import socket
import asyncio
import time

LIZ_IP = "192.168.8.135"
MY_IP = "192.168.8.220"
PORT = 12346
LAPTOP_IP = "192.168.8.199"


async def tone_for_duration(freq, duration, pin):
    select_pin(pin)
    start=time.time()
    while start+duration>time.time():
        ret = write_gpio(pin, 1)
        await asyncio.sleep((1/freq*2))
        ret = write_gpio(pin, 0)
        await asyncio.sleep(1/(freq*2))

def wait_for_button(btns):
    while True:
        time.sleep(0.01)
        res = btns.read()
        if res & 0b0001:
            return 0
        if res & 0b0010:
            return 1
        if res & 0b0100:
            return 2
        if res & 0b1000:
            return 3

async def client_main():
    global base
    btns = base.btns_gpio
    while wait_for_button(btns)!=0:
        # wait for button 0 to start connection
        pass
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((LIZ_IP, PORT))
    while True:
        match wait_for_button(btns):
            case 1:
                # buzz
                sock.send(b"BUZZ!")
            case 3:
                break
            case _:
                print("wrong button")

    sock.close()

def server_proc():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((MY_IP, PORT))
    try:
        sock.listen(2)
        con, adr = sock.accept()
        msg = con.recv(1024)
        while len(msg)>0:
            if msg.startswith("buzz"):
                print("server got buzz")
                asyncio.run(tone_for_duration(5000, 1, 0))

            msg = con.recv(1024)
    finally:
        con.close()


def client_proc():
    
    asyncio.run(client_main)


client_p = mp.Process(target=client_proc)
server_p = mp.Process(target=server_proc)

client_p.start()
server_p.start()

client_p.join()
server_p.join()


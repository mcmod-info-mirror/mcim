import aria2p
import json
import os

MOUNT_POINT = "路径/modrinth"

DATA_PATH = "data150000-end.json"

# def aria2_deamin():
#     os.system("aria2c --enable-rpc --max-concurrent-downloads=64 --rpc-listen-port=6800") # 一直重启 aria2c rpc服务

aria2_api = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

for i in range(255):
    os.makedirs(os.path.join(MOUNT_POINT, hex(i)[:2]), exist_ok=True)

print(aria2_api.get_stats().__dict__)

def download():
    if not os.path.exists(MOUNT_POINT):
        print(f"Mount point {MOUNT_POINT} not found.")
        exit(1)
    if not os.path.exists(DATA_PATH):
        print(f"Data file {DATA_PATH} not found.")
        exit(1)


    with open(DATA_PATH) as f:
        data = json.load(f)
        for file in data.values():
            if not os.path.exists(os.path.join(MOUNT_POINT, file["sha1"][:2], file["sha1"])):
                aria2_api.add(file["url"], options={"dir": f'{MOUNT_POINT}/{file["sha1"][:2]}', "out": file["sha1"]})

                # w = 0
                # while True:
                #     if aria2_api.get_stats().num_waiting > 100: # 等待队列超过100个，等待
                #         time.sleep(DELAY)
                #         w += 1
                #         if w > 10: # 等待超过50秒，检查 rpc
                #             i = 0
                #             while i< 5*8: # 五秒内速度小于1MB/s
                #                 if aria2_api.get_stats().download_speed < 1024*1024:
                #                     time.sleep(0.25)
                #                     i += 1
                #             else:
                #                 aria2_api.stop_listening()
                #                 aria2_deamin()
                #     else:
                #         break
if __name__ == "__main__":
    download()
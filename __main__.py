from nordicsemi.dfu_update import update

if __name__ == '__main__':
    update("test.zip", ('192.168.8.200', 5000))
    # update("test.zip", ('192.168.8.183', 5000))
    # update("test.zip", ('192.168.8.169', 8089))
    # update("test.zip", ('192.168.8.121', 20001))
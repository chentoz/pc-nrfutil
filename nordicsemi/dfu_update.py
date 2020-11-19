from socket import socket
from nordicsemi.dfu.dfu_transport_network import DfuTransportUDP
from nordicsemi.dfu.dfu_transport import DfuTransport, DfuEvent, TRANSPORT_LOGGING_LEVEL
from nordicsemi.dfu.dfu import Dfu

import logging
logger = logging.getLogger(__name__)

global_bar = None
def update_progress(progress=0):
    if global_bar:
        global_bar.update(progress)

def update(package, outgoing_ip, sock):
    """Perform a Device Firmware Update on a device with a bootloader that supports UART serial DFU."""
    do_network(package, outgoing_ip, sock)

def do_network(package, outgoing_ip, sock):
    logger.info("Doing network ")

    udp_backend = DfuTransportUDP(outgoing_ip, sock,
                                  flow_control=False, prn=0, do_ping=True,
                                  timeout=1.0)

    udp_backend.register_events_callback(
        DfuEvent.PROGRESS_EVENT, update_progress)

    dfu = Dfu(zip_file_path=package, dfu_transport=udp_backend,
              connect_delay=3)
    dfu.dfu_send_images()

    """     if logger.getEffectiveLevel() > logging.INFO:
        with click.progressbar(length=dfu.dfu_get_total_size()) as bar:
            global global_bar
            global_bar = bar
            dfu.dfu_send_images()
    else:
 """
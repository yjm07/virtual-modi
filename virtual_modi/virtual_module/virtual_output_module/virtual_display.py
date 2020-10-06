
from virtual_modi.virtual_module.virtual_module import VirtualModule

from virtual_modi.utility.message_util import decode_message
from virtual_modi.utility.message_util import unpack_data


class VirtualDisplay(VirtualModule):

    def __init__(self):
        super(VirtualDisplay, self).__init__()
        self.uuid = self.generate_uuid(0x4000)

        self.text_buffer = []
        self.text = ''
        self.position = 0, 0

    def process_set_property_message(self, message):
        cmd, sid, did, data, dlc = decode_message(message)
        display_value = bytes(unpack_data(data))
        if cmd == 17:
            text = [chr(t) for t in display_value]

            self.text_buffer.append(text)
            if text[-1] == '\0':
                self.text = ''.join(self.text_buffer)
                self.text_buffer.clear()
        elif cmd == 21:
            clear_status = int.from_bytes(display_value[0:2], byteorder='little')
            if not clear_status:
                self.text = ''
            else:
                self.text_buffer.clear()

    def run(self):
        self.send_health_message()

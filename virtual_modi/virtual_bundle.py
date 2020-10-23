
import os
import time
import threading as th

from random import randint
from importlib.util import find_spec

from virtual_modi.util.message_util import decode_message


class VirtualBundle:
    """
    A virtual interface between a local machine and the virtual network module
    """

    def __init__(self, modules=None, gui=False, verbose=False):
        # Init flag to check if the program is running on GUI
        self.gui = gui

        # Init flag decide whether to suppress messages or not
        self.verbose = verbose

        # Init flag to notify associated threads
        self.running = True

        # Create virtual modules have been initialized
        self.attached_virtual_modules = list()

        # Messages to be sent out to the local machine (i.e. PC)
        self.external_messages = list()

        # Start module initialization by creating a network module at first
        vnetwork = self.create_new_module('network')

        # If no modules are specified, create network, button and led modules
        if not gui and not modules:
            print('Generating a default set of virtual modules...')
            vbutton = self.create_new_module('button')
            vled = self.create_new_module('led')

            vnetwork.attach_module('r', vbutton)
            vbutton.attach_module('b', vled)

        # Given modules only e.g. modules = ["button", "dial", "led"]
        elif isinstance(modules[0], str) and ',' not in modules[0]:

            if len(modules) > 10:
                raise ValueError("Virtual mode supports up to 10 modules!!")

            # Create instances of the specified modules
            for module_name in modules:
                self.create_new_module(module_name.lower())

            # Unfortunately, the topology of the virtual modules are random
            directions = ('r', 't', 'l', 'b')
            for i, module in enumerate(self.attached_virtual_modules):
                # Initiate a module to be attached to the current module
                if i == (len(self.attached_virtual_modules) - 1):
                    break
                next_module = self.attached_virtual_modules[i+1]

                # Attach if current module has nothing on its random direction
                random_direction = directions[randint(0, 3)]
                while module.topology.get(random_direction):
                    random_direction = directions[randint(0, 3)]
                module.attach_module(random_direction, next_module)

        # Given both module and directions e.g. modules=["button, r", "led, t"]
        elif isinstance(modules[0], str) and ',' in modules[0]:
            prev_module = vnetwork
            for s in modules:
                direction, module = s.replace(' ', '').split(',')
                module_instance = self.create_new_module(module)
                prev_module.attach_module(direction, module_instance)
                prev_module = module_instance

    def open(self):
        # Start all threads
        th.Thread(
            target=self.collect_module_messages, args=[0.1], daemon=True
        ).start()

    def close(self):
        # Kill all threads
        self.running = False

    def send(self):
        msg_to_send = ''.join(self.external_messages)
        self.external_messages = []
        return msg_to_send.encode()

    def recv(self, msg):
        _, _, did, *_ = decode_message(msg)
        if did == 4095:
            for current_module in self.attached_virtual_modules:
                current_module.process_received_message(msg)
        else:
            for current_module in self.attached_virtual_modules:
                curr_module_id = current_module.id
                if curr_module_id == did:
                    current_module.process_received_message(msg)
                    break
            else:
                print('Cannot find a virtual module with id:', did)

    #
    # Helper functions below
    #
    def create_new_module(self, module_type):
        module_template = self.create_module_from_type(module_type)
        module_instance = module_template()
        self.attached_virtual_modules.append(module_instance)
        if self.verbose:
            print(f"{str(module_instance)} has been created!")
        return module_instance

    @staticmethod
    def create_module_from_type(module_type):
        module_type = module_type[0].lower() + module_type[1:]
        module_path = 'virtual_modi.virtual_module.virtual'
        module_module_template = (
            find_spec(f'{module_path}_input_module.virtual_{module_type}')
            or find_spec(f'{module_path}_output_module.virtual_{module_type}')
            or find_spec(f'{module_path}_setup_module.virtual_{module_type}')
        )
        module_module = module_module_template.loader.load_module(
            module_module_template.name
        )
        module_name = 'Virtual' + module_type[0].upper() + module_type[1:]
        return getattr(module_module, module_name)

    def collect_module_messages(self, delay):
        while self.running:
            # Collect messages generated from each module
            for current_module in self.attached_virtual_modules:
                # Generate module message
                current_module.send_health_message()
                current_module.run()

                # Collect the generated module message
                self.external_messages.extend(current_module.messages_to_send)
                current_module.messages_to_send.clear()
            time.sleep(delay)

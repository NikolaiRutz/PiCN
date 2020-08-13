import time

from typing import List
from PiCN.Layers.ICNLayer.PendingInterestTable.PendingInterestTableMemoryExact import PendingInterstTableMemoryExact, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.PendingInterestTable.BasePendingInterestTable import BasePendingInterestTable, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.ForwardingInformationBase import ForwardingInformationBaseEntry
from PiCN.Packets import Interest, Name
import re

"""PIT for Pub/Sub Model"""


class PendingInterestTableMemoryExactPubSub(PendingInterstTableMemoryExact):

    def __init__(self, pit_timeout: int = 10, pit_retransmits: int = 3, pub_sub: bool = False):
        BasePendingInterestTable.__init__(self, pit_timeout=pit_timeout, pit_retransmits=pit_retransmits)
        self.pub_sub = pub_sub

    # regex expression noch nicht ganz richtig (auch true wenn kein Wert in den Klammern steht)
    def is_pub_sub(self, name: Name) -> bool:
        sub_name = name.components[-1].decode("utf-8")
        return bool(re.search("subscribe\(\d*\)", sub_name))

    def add_pit_entry(self, name, faceid: int, interest: Interest = None, local_app=False):
        for pit_entry in self.container:
            if pit_entry.name == name:
                if faceid in pit_entry.face_id and local_app in pit_entry.local_app:
                    return
                self.container.remove(pit_entry)
                pit_entry._faceids.append(faceid)
                pit_entry._local_app.append(local_app)
                pit_entry.pub_sub = self.is_pub_sub(name)
                self.container.append(pit_entry)
                return
        # check if fisrt entry in container is a PS entry
        self.container.append(
            PendingInterestTableEntry(name, faceid, interest, local_app, pub_sub=True))

    def extract_sub_value(self, name: Name) -> int:
        return int(re.findall('\d+', name.components[-1].decode("utf-8"))[0])

    def remove_pit_entry(self, name: Name):
        to_remove = []
        for pit_entry in self.container:
            if (pit_entry.name == name):
                if not pit_entry.pub_sub:
                    continue
                to_remove.append(pit_entry)
        for r in to_remove:
            self.container.remove(r)

    #TODO: container mit PIT entries bleibt immer leer
    def find_pit_entry(self, name: Name) -> PendingInterestTableEntry:
        for pit_entry in self.container:
            if (pit_entry.name == name):
                return pit_entry
            print("here")
            if pit_entry.pub_sub:
                sub_entry_name = pit_entry.name
                sub_entry_name.components.pop()
                for i in range(self.extract_sub_value(pit_entry.name)):
                    if (sub_entry_name == name):
                        return pit_entry
                    sub_entry_name.components.pop()
        return None

    # add pub sub
    def ageing(self) -> List[PendingInterestTableEntry]:
        return None

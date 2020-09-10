import time

from typing import List
from PiCN.Layers.ICNLayer.PendingInterestTable.PendingInterestTableMemoryExact import PendingInterstTableMemoryExact, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.PendingInterestTable.BasePendingInterestTable import BasePendingInterestTable, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.ForwardingInformationBase import ForwardingInformationBaseEntry
from PiCN.Packets import Interest, Name
import re
import copy

"""PIT for Pub/Sub Model"""


class PendingInterestTableMemoryExactPubSub(PendingInterstTableMemoryExact):

    def __init__(self, pit_timeout: int = 10, pit_retransmits: int = 3, pub_sub: int = -1):
        BasePendingInterestTable.__init__(self, pit_timeout=pit_timeout, pit_retransmits=pit_retransmits)
        self.pub_sub = pub_sub

    #TODO: clean this code
    # regex expression noch nicht ganz richtig (auch true wenn kein Wert in den Klammern steht)
    def is_pub_sub(self, name: Name) -> bool:
        sub_name = name.components[-1].decode("utf-8")
        return bool(re.search("subscribe\(\d*\)", sub_name))

    # TODO: PIT entry wird nicht richtig ertstellt wenn subscribe value zu hoch ist!
    def add_pit_entry(self, name, faceid: int, interest: Interest = None, local_app=False):
        for pit_entry in self.container:
            if pit_entry.name == name:
                if faceid in pit_entry.face_id and local_app in pit_entry.local_app:
                    return
                self.container.remove(pit_entry)
                pit_entry._faceids.append(faceid)
                pit_entry._local_app.append(local_app)
                if self.extract_sub_value(name) >= 0:
                    pit_entry.pub_sub = self.extract_sub_value(name)
                    name.components.pop()
                self.container.append(pit_entry)
                return

        pub_sub_value = -1
        if self.extract_sub_value(name) >= 0:
            pub_sub_value = self.extract_sub_value(name)
            name.components.pop()
        self.container.append(
            PendingInterestTableEntry(name, faceid, interest, local_app, pub_sub=pub_sub_value))

    def extract_sub_value(self, name: Name) -> int:
        return int(re.findall('\d+', name.components[-1].decode("utf-8"))[0])

    def remove_pit_entry(self, name: Name):
        to_remove = []
        for pit_entry in self.container:
            if (pit_entry.name == name):
                if pit_entry.pub_sub >= 0:
                    continue
                to_remove.append(pit_entry)
        for r in to_remove:
            self.container.remove(r)

    def find_pit_entry(self, name: Name) -> PendingInterestTableEntry:
        for pit_entry in self.container:
            if (pit_entry.name == name):
                return pit_entry
            if (self.is_pub_sub(name)):
                sub_entry_name = copy.deepcopy(name)
                sub_entry_name.components.pop()
                #TODO: schauen ob auch der sub value gleich sein muss
                if(sub_entry_name == pit_entry.name):
                    return pit_entry
            #2 cases. einmal interest mit sub hinten dran -> soll auch pitentry returnen
            #und einmal content der zum client zurückfinden soll
            if pit_entry.pub_sub >= 0:
                sub_entry_name = copy.deepcopy(pit_entry.name)
                if len(sub_entry_name) < len(pit_entry.name):
                    return None
                for i in range(pit_entry.pub_sub):
                    if (sub_entry_name == pit_entry.name):
                        return pit_entry
                    sub_entry_name.components.pop()
        return None

    def ageing(self) -> List[PendingInterestTableEntry]:
        cur_time = time.time()
        remove = []
        updated = []
        for pit_entry in self.container:
            if pit_entry.pub_sub >= 0:
                continue
            if pit_entry.timestamp + self._pit_timeout < cur_time and pit_entry.retransmits > self._pit_retransmits:
                remove.append(pit_entry)
            else:
                pit_entry.retransmits = pit_entry.retransmits + 1
                updated.append(pit_entry)
        for pit_entry in remove:
            self.remove_pit_entry(pit_entry.name)
        for pit_entry in updated:
            self.remove_pit_entry(pit_entry.name)
            self.container.append(pit_entry)
        return updated, remove
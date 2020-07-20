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

    def __init__(self, name: Name, faceid: int, interest: Interest = None, local_app: bool = False,
                 fib_entries_already_used: List[ForwardingInformationBaseEntry] = None, faces_already_nacked=None,
                 number_of_forwards=0, pub_sub: bool = False):
        BasePendingInterestTable.__init__(name, faceid, interest, local_app, fib_entries_already_used,
                                          faces_already_nacked, number_of_forwards)
        self.pub_sub = pub_sub

    # regex expression noch nicht ganz richtig (auch true wenn kein Wert in den Klammern steht)
    def is_pub_sub(self, name: Name) -> bool:
        if re.search("/subscribe\(\d*\)", name.to_string()):
            return True

    def add_pit_entry(self, name, faceid: int, interest: Interest = None, local_app=False):
        for pit_entry in self.container:
            if pit_entry.name == name:
                if faceid in pit_entry.face_id and local_app in pit_entry.local_app:
                    return
                self.container.remove(pit_entry)
                pit_entry._faceids.append(faceid)
                pit_entry._local_app.append(local_app)
                self.container.append(pit_entry)
                return
            # falls pub-sub dann bool auf true; per default false
            self.pub_sub = self.is_pub_sub(name)
        self.container.append(PendingInterestTableEntry(name, faceid, interest, local_app))

    def remove_pit_entry(self, name: Name):
        to_remove = []
        # checken ob es pub sub ist; über alles iterieren
        for pit_entry in self.container:
            if (pit_entry.name == name):
                if not self.pub_sub:
                    continue
                to_remove.append(pit_entry)
        for r in to_remove:
            self.container.remove(r)

    # pub sub longest prefix bzw. subscribe(3)
    #herausfiltern des Integers bei subscribe
    def find_pit_entry(self, name: Name) -> PendingInterestTableEntry:
        return None

    # add pub sub
    def ageing(self) -> List[PendingInterestTableEntry]:
        return None

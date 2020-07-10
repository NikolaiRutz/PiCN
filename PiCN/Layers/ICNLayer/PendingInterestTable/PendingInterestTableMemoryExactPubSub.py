import time

from typing import List
from PiCN.Layers.ICNLayer.PendingInterestTable.PendingInterestTableMemoryExact import PendingInterstTableMemoryExact, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.PendingInterestTable.BasePendingInterestTable import BasePendingInterestTable, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.ForwardingInformationBase import ForwardingInformationBaseEntry
from PiCN.Packets import Interest, Name


"""PIT for Pub/Sub Model"""
class PendingInterestTableMemoryExactPubSub(PendingInterstTableMemoryExact):

#warum muss add verändert werden?
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
        self.container.append(PendingInterestTableEntry(name, faceid, interest, local_app))

#wenn pub_sub PIT dann nicht removen
    def remove_pit_entry(self, name: Name, pub_sub: bool):
        if pub_sub:
            return
        to_remove = []

        for pit_entry in self.container:
            if (pit_entry.name == name):
                to_remove.append(pit_entry)
        for r in to_remove:
            self.container.remove(r)
